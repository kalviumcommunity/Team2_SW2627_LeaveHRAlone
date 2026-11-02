import re
from typing import Any, Dict, List, Optional

from app.rag.generation.base import BaseLLMProvider


REWRITE_SYSTEM_PROMPT = """You are an HR query pre-processor.
Given the recent conversation history between an employee and an HR assistant, reformulate the employee's follow-up question into a clear, standalone search query.
- Resolve any ambiguous pronouns (such as "it", "them", "these", "that", "those", "they").
- Include the relevant policy topic (e.g., annual leave, sick leave, health insurance, maternity).
- Keep the standalone query concise and factual.
- Return ONLY the rewritten question string, without any commentary or explanation.
"""


def rule_based_rewrite(question: str, history: List[Dict[str, str]], region: str) -> str:
    """Fast deterministic rule-based follow-up query rewriting."""
    q_lower = question.lower().strip()

    # If already fully specified or no history, return clean query
    if not history:
        return question

    # Extract last user question and last assistant answer
    last_user_msg = ""
    last_assistant_msg = ""
    for msg in reversed(history[-4:]):
        role = msg.get("role")
        content = msg.get("content", "")
        if role == "user" and not last_user_msg:
            last_user_msg = content
        elif role == "assistant" and not last_assistant_msg:
            last_assistant_msg = content

    combined_context = f"{last_user_msg} {last_assistant_msg}".lower()

    # Identify preceding topic
    topic = ""
    if "annual leave" in combined_context or "paid leave" in combined_context or "pto" in combined_context:
        topic = "annual leave"
    elif "sick leave" in combined_context or "casual leave" in combined_context:
        topic = "sick leave"
    elif "maternity" in combined_context or "parental" in combined_context or "paternity" in combined_context:
        topic = "parental leave"
    elif "insurance" in combined_context or "medical" in combined_context or "gmc" in combined_context:
        topic = "health insurance"
    elif "remote" in combined_context or "wfh" in combined_context:
        topic = "remote work policy"

    # Common follow-up patterns
    if re.search(r"\b(carry\s+(them\s+)?forward|carry\s+over)\b", q_lower):
        target_topic = topic or "annual leave"
        return f"Can an employee in {region} carry forward unused {target_topic}?"

    if re.search(r"\b(who\s+is\s+eligible|eligibility|am\s+i\s+eligible)\b", q_lower):
        target_topic = topic or "policy benefits"
        return f"What are the eligibility requirements for {target_topic} in {region}?"

    if re.search(r"\b(what\s+about\s+(them|it|that))\b", q_lower):
        target_topic = topic or "benefits"
        return f"What are the policy guidelines for {target_topic} in {region}?"

    if re.search(r"\b(how\s+do\s+i\s+apply|application\s+process)\b", q_lower):
        target_topic = topic or "leave"
        return f"How does an employee in {region} apply for {target_topic}?"

    return question


async def rewrite_query(
    question: str,
    history: List[Dict[str, str]],
    region: str,
    llm_provider: BaseLLMProvider,
) -> str:
    """Rewrite follow-up questions using conversation history and LLM or rules."""
    if not history:
        return question

    # If question contains pronouns and we have history, rewrite it
    has_pronoun = bool(re.search(r"\b(it|them|they|these|those|that|this|there|such)\b", question.lower()))
    is_short = len(question.split()) <= 6

    if not has_pronoun and not is_short:
        return question

    # Format history turns (last 4 messages)
    history_turns = []
    for msg in history[-4:]:
        role = "Employee" if msg.get("role") == "user" else "Assistant"
        content = msg.get("content", "").replace("\n", " ")
        history_turns.append(f"{role}: {content}")

    history_str = "\n".join(history_turns)
    prompt = f"Employee Region: {region}\n\nConversation History:\n{history_str}\n\nFollow-up Question: {question}\n\nStandalone Query:"

    try:
        response = await llm_provider.generate_async(
            prompt=prompt,
            system_prompt=REWRITE_SYSTEM_PROMPT,
            temperature=0.0,
            max_tokens=60,
        )
        cleaned = response.strip().strip('"').strip("'")
        if cleaned and len(cleaned) > 5 and "{" not in cleaned:
            return cleaned
    except Exception:
        pass

    return rule_based_rewrite(question, history, region)


class QueryRewriter:
    """Query rewriter for follow-up pronoun resolution and context grounding."""

    def rewrite(
        self,
        question: str,
        history: Optional[List[Dict[str, str]]] = None,
        region: str = "India",
    ) -> str:
        return rule_based_rewrite(question, history or [], region)

    async def rewrite_async(
        self,
        question: str,
        history: Optional[List[Dict[str, str]]] = None,
        region: str = "India",
        llm_provider: Optional[BaseLLMProvider] = None,
    ) -> str:
        if llm_provider and history:
            return await rewrite_query(question, history, region, llm_provider)
        return rule_based_rewrite(question, history or [], region)


query_rewriter = QueryRewriter()
