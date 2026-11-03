"""
LeaveHRAlone AI — Chat / Query Route
Implements the core RAG pipeline: rewrite → retrieve → generate → cite → respond.
"""
import asyncio
import json
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Any, AsyncGenerator, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy import desc, select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.config import settings
from app.db.models import AuditLog, Conversation, Message, User, UserRole
from app.db.session import get_db
from app.rag.generation import get_llm_provider
from app.rag.retrieval.engine import retrieval_engine
from app.rag.retrieval.query_rewriter import query_rewriter
from app.rag.verification import verify_numeric_grounding
from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    ChatSource,
    ConversationSummary,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Chat"])


def _build_rag_prompt(
    query: str,
    region: str,
    chunks,
) -> str:
    """Assemble the RAG prompt with retrieved policy context."""
    context_parts = []
    for i, chunk in enumerate(chunks, 1):
        context_parts.append(
            f"[Document: {chunk.document_title}, "
            f"Section: {chunk.section}, "
            f"Page: {chunk.page_number}, "
            f"Version: {chunk.version}, "
            f"Region: {chunk.region}]\n{chunk.chunk_text}"
        )

    context = "\n\n---\n\n".join(context_parts) if context_parts else "No relevant policy documents found."

    return f"""You are LeaveHRAlone AI, a region-aware HR policy assistant for the {region} office.
Answer the employee's question strictly based on the following HR policy context.
Format your answer in two distinct sections:
1. Provide a direct, clear, plain-language answer addressing the question first.
2. Immediately follow with the exact supporting excerpt from the official policy document formatted as a blockquote:
   > 📌 **Official Policy Excerpt (<Document Title>, <Section>):**
   > "<Exact quoted policy sentence(s)>"
Do NOT hallucinate or fabricate information not present in the context.
If the context is insufficient, indicate that HR should be contacted.
Respond in JSON format: {{"answer": "...", "confidence": "high|medium|low|none", "sources": [], "requires_hr": false, "refusal": false}}

=== POLICY CONTEXT ===
{context}
=== USER QUESTION ===
{query}"""


def _parse_llm_response(raw: str, chunks, user_region: str) -> Dict[str, Any]:
    """Parse and validate the LLM JSON response."""
    try:
        raw_clean = raw.strip()
        if raw_clean.startswith("```"):
            lines = raw_clean.split("\n")
            raw_clean = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])
        parsed = json.loads(raw_clean)
    except (json.JSONDecodeError, ValueError):
        parsed = {
            "answer": raw,
            "confidence": "low",
            "sources": [],
            "requires_hr": True,
            "refusal": False,
        }

    # Build structured sources from retrieved chunks
    sources = []
    for chunk in chunks[:5]:
        sources.append(
            ChatSource(
                document_title=chunk.document_title,
                section=chunk.section,
                page_number=chunk.page_number,
                version=chunk.version,
                region=chunk.region,
                category=chunk.category,
                similarity_score=chunk.similarity_score,
            )
        )

    parsed["sources"] = sources
    return parsed


@router.post("/chat", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Core RAG pipeline endpoint:
    1. Query rewriting for better retrieval
    2. Region-aware 3-tier retrieval from Qdrant
    3. LLM generation with grounded context
    4. Structured citation extraction
    5. Conversation history persistence
    """
    start_ms = int(time.time() * 1000)

    # Determine region & role overrides
    if current_user and current_user.role in [UserRole.HR_ADMIN.value, UserRole.SUPER_ADMIN.value] and body.region:
        user_region = body.region
    else:
        user_region = current_user.region if current_user else (body.region or "India")

    employee_type = getattr(current_user, "employment_type", "All")

    # ---- 1. Query Rewriting ----
    try:
        rewritten_query = query_rewriter.rewrite(body.query)
    except Exception:
        rewritten_query = body.query

    # ---- 2. Retrieval ----
    try:
        chunks = retrieval_engine.retrieve(
            query=rewritten_query,
            user_region=user_region,
            employee_type=employee_type,
            top_k=body.top_k,
        )
    except Exception as e:
        logger.error("Retrieval error: %s", e)
        chunks = []

    # Relevance threshold check: if top chunk score < threshold, return refusal
    top_score = chunks[0].similarity_score if chunks else 0.0
    if not chunks or top_score < settings.rag_similarity_threshold:
        parsed = {
            "answer": "I couldn't find this information in the official policy documents for your region. Please contact HR for assistance.",
            "confidence": "low",
            "sources": [],
            "requires_hr": True,
            "refusal": False,
        }
    else:
        # ---- 3. Build Prompt & Generate ----
        prompt = _build_rag_prompt(query=body.query, region=user_region, chunks=chunks)
        llm = get_llm_provider()

        try:
            raw_response = await llm.generate_async(prompt)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"LLM generation failed: {str(e)}",
            )

        # ---- 4. Parse & Build Response ----
        parsed = _parse_llm_response(raw_response, chunks, user_region)

        # Post-generation numeric fact grounding check
        context_str = "\n".join(ch.chunk_text for ch in chunks)
        is_grounded, ungrounded_numbers = verify_numeric_grounding(parsed.get("answer", ""), context_str)
        if not is_grounded:
            logger.warning("Numeric grounding check flagged unverified numbers: %s", ungrounded_numbers)
            parsed["confidence"] = "low"
            parsed["requires_hr"] = True

    elapsed_ms = int(time.time() * 1000) - start_ms

    # ---- 5. Persist to Conversation History (requires authenticated user) ----
    conversation = None
    if current_user:
        if body.conversation_id:
            try:
                result = await db.execute(
                    select(Conversation).where(
                        Conversation.id == uuid.UUID(body.conversation_id),
                        Conversation.user_id == current_user.id,
                    )
                )
                conversation = result.scalar_one_or_none()
            except Exception:
                conversation = None

        if conversation is None:
            conversation = Conversation(
                id=uuid.uuid4(),
                user_id=current_user.id,
                title=body.query[:80],
                region_snapshot=user_region,
            )
            db.add(conversation)
            await db.flush()

        # Add user message
        user_msg = Message(
            id=uuid.uuid4(),
            conversation_id=conversation.id,
            role="user",
            content=body.query,
            confidence="none",
        )
        db.add(user_msg)

        # Add assistant message with sources in raw_rag_response
        sources_json = [s.model_dump() for s in parsed.get("sources", [])]
        assistant_msg = Message(
            id=uuid.uuid4(),
            conversation_id=conversation.id,
            role="assistant",
            content=parsed.get("answer", ""),
            confidence=parsed.get("confidence", "low"),
            raw_rag_response={
                "sources": sources_json,
                "requires_hr": parsed.get("requires_hr", False),
                "refusal": parsed.get("refusal", False),
            },
        )
        db.add(assistant_msg)

        conversation.updated_at = datetime.now(timezone.utc)

        # Audit log
        audit = AuditLog(
            id=uuid.uuid4(),
            user_id=current_user.id,
            action="CHAT_QUERY",
            resource_type="conversation",
            resource_id=str(conversation.id),
            details={
                "query": body.query[:200],
                "region": user_region,
                "confidence": parsed.get("confidence"),
                "sources_count": len(parsed.get("sources", [])),
                "processing_time_ms": elapsed_ms,
            },
        )
        db.add(audit)

        try:
            await db.commit()
        except Exception:
            await db.rollback()

    return ChatResponse(
        answer=parsed.get("answer", "Unable to generate a response."),
        confidence=parsed.get("confidence", "low"),
        sources=parsed.get("sources", []),
        requires_hr=parsed.get("requires_hr", False),
        refusal=parsed.get("refusal", False),
        conversation_id=str(conversation.id) if conversation else str(uuid.uuid4()),
        query=body.query,
        region=user_region,
        processing_time_ms=elapsed_ms,
    )


@router.get("/conversations", response_model=List[ConversationSummary])
async def list_conversations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(default=20, le=50),
) -> Any:
    """Retrieve the current user's conversation history summaries."""
    result = await db.execute(
        select(Conversation)
        .where(Conversation.user_id == current_user.id)
        .order_by(desc(Conversation.updated_at))
        .limit(limit)
    )
    conversations = result.scalars().all()

    summaries = []
    for conv in conversations:
        msg_result = await db.execute(
            select(func.count(Message.id)).where(Message.conversation_id == conv.id)
        )
        msg_count = msg_result.scalar() or 0
        summaries.append(
            ConversationSummary(
                id=conv.id,
                title=conv.title,
                created_at=conv.created_at,
                updated_at=conv.updated_at,
                message_count=msg_count,
            )
        )

    return summaries


@router.get("/conversations/{conv_id}")
async def get_conversation(
    conv_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Retrieve full conversation details including messages and sources."""
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conv_id,
            Conversation.user_id == current_user.id,
        )
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    msg_result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conv.id)
        .order_by(Message.created_at.asc())
    )
    messages = msg_result.scalars().all()

    formatted_messages = []
    for m in messages:
        sources = []
        if m.raw_rag_response and "sources" in m.raw_rag_response:
            sources = m.raw_rag_response["sources"]

        formatted_messages.append(
            {
                "id": str(m.id),
                "role": m.role,
                "content": m.content,
                "confidence": m.confidence,
                "sources": sources,
                "created_at": m.created_at.isoformat(),
            }
        )

    return {
        "id": str(conv.id),
        "title": conv.title,
        "region_snapshot": conv.region_snapshot,
        "created_at": conv.created_at.isoformat(),
        "updated_at": conv.updated_at.isoformat(),
        "messages": formatted_messages,
    }


@router.delete("/conversations/{conv_id}")
async def delete_conversation(
    conv_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Delete a conversation and all its messages."""
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conv_id,
            Conversation.user_id == current_user.id,
        )
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    await db.delete(conv)
    await db.commit()
    return {"message": "Conversation deleted"}


@router.post("/chat/stream")
async def chat_stream(
    body: ChatRequest,
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Server-Sent Events (SSE) streaming endpoint for LeaveHRAlone AI answers.
    Streams answer tokens, followed by a 'done' event with citations and confidence.
    """
    # 1. Determine region & role overrides
    if current_user and current_user.role in [UserRole.HR_ADMIN.value, UserRole.SUPER_ADMIN.value] and body.region:
        user_region = body.region
    else:
        user_region = current_user.region if current_user else (body.region or "India")

    employee_type = getattr(current_user, "employment_type", "All")

    # 2. Query Rewriting & Retrieval
    try:
        rewritten_query = query_rewriter.rewrite(body.query)
    except Exception:
        rewritten_query = body.query

    try:
        chunks = retrieval_engine.retrieve(
            query=rewritten_query,
            user_region=user_region,
            employee_type=employee_type,
            top_k=body.top_k,
        )
    except Exception as e:
        logger.error("Retrieval error in stream: %s", e)
        chunks = []

    async def event_generator() -> AsyncGenerator[str, None]:
        # Relevance threshold check
        top_score = chunks[0].similarity_score if chunks else 0.0
        if not chunks or top_score < settings.rag_similarity_threshold:
            refusal_text = (
                "I couldn't find this information in the official policy documents for your region. "
                "Please reach out to HR for clarification."
            )
            for word in refusal_text.split(" "):
                yield f"data: {json.dumps({'token': word + ' '})}\n\n"
                await asyncio.sleep(0.02)

            yield f"data: {json.dumps({'done': True, 'answer': refusal_text, 'confidence': 'low', 'sources': [], 'requires_hr': True})}\n\n"
            return

        # Build prompt & call LLM
        prompt = _build_rag_prompt(query=body.query, region=user_region, chunks=chunks)
        llm = get_llm_provider()

        try:
            raw_response = await llm.generate_async(prompt)
            parsed = _parse_llm_response(raw_response, chunks, user_region)
        except Exception as e:
            logger.error("Generation error in stream: %s", e)
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
            return

        # Numeric fact checking
        context_str = "\n".join(ch.chunk_text for ch in chunks)
        is_grounded, ungrounded_numbers = verify_numeric_grounding(parsed.get("answer", ""), context_str)
        if not is_grounded:
            parsed["confidence"] = "low"
            parsed["requires_hr"] = True

        answer_text = parsed.get("answer", "")
        # Stream answer tokens
        words = answer_text.split(" ")
        for i, word in enumerate(words):
            token = word + (" " if i < len(words) - 1 else "")
            yield f"data: {json.dumps({'token': token})}\n\n"
            await asyncio.sleep(0.015)

        # Final metadata event with sources and confidence
        sources_payload = [
            s.model_dump() if hasattr(s, "model_dump") else s
            for s in parsed.get("sources", [])
        ]
        done_payload = {
            "done": True,
            "answer": answer_text,
            "confidence": parsed.get("confidence", "low"),
            "sources": sources_payload,
            "requires_hr": parsed.get("requires_hr", False),
        }
        yield f"data: {json.dumps(done_payload)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )

