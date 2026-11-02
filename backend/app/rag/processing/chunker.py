import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import tiktoken

CHUNK_SIZE = 500
CHUNK_OVERLAP = 75
TOKENIZER_NAME = "cl100k_base"


@dataclass
class ProcessedChunk:
    chunk_index: int
    text: str
    token_count: int
    page_number: int
    section: str
    start_token: int
    end_token: int


def get_tokenizer(encoding_name: str = TOKENIZER_NAME) -> tiktoken.Encoding:
    """Return the tiktoken encoding instance."""
    return tiktoken.get_encoding(encoding_name)


def count_tokens(text: str, tokenizer: Optional[tiktoken.Encoding] = None) -> int:
    """Count tokens in string using configured tokenizer."""
    tok = tokenizer or get_tokenizer()
    return len(tok.encode(text))


def chunk_text(
    text: str,
    chunk_size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP,
    page_number: int = 1,
    section: str = "General",
    tokenizer: Optional[tiktoken.Encoding] = None,
) -> List[ProcessedChunk]:
    """Split text into token-bounded chunks (500-800 tokens) with overlap, never splitting mid-sentence."""
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than zero.")
    if overlap < 0:
        raise ValueError("overlap cannot be negative.")
    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size.")

    tok = tokenizer or get_tokenizer()
    tokens = tok.encode(text)

    if not tokens:
        return []

    chunks: List[ProcessedChunk] = []
    start = 0

    while start < len(tokens):
        raw_end = min(start + chunk_size, len(tokens))

        # Sentence boundary detection: if not at the end of text, find last sentence termination
        end = raw_end
        if raw_end < len(tokens):
            candidate_text = tok.decode(tokens[start:raw_end])
            # Search for sentence terminators (. ! ? \n\n) within the latter 30% of candidate
            min_boundary_pos = int(len(candidate_text) * 0.70)
            boundary_matches = [
                m.end() for m in re.finditer(r"(\. |\.\n|\? |\!\n|\n\n|\n[A-Z0-9])", candidate_text)
                if m.end() >= min_boundary_pos
            ]
            if boundary_matches:
                # Snap to the closest sentence terminator
                best_char_pos = boundary_matches[-1]
                snapped_text = candidate_text[:best_char_pos].strip()
                snapped_tokens = tok.encode(snapped_text)
                if len(snapped_tokens) >= int(chunk_size * 0.60):
                    end = start + len(snapped_tokens)

        chunk_tokens = tokens[start:end]
        chunk_str = tok.decode(chunk_tokens).strip()

        if chunk_str:
            chunks.append(
                ProcessedChunk(
                    chunk_index=len(chunks),
                    text=chunk_str,
                    token_count=len(chunk_tokens),
                    page_number=page_number,
                    section=section,
                    start_token=start,
                    end_token=end,
                )
            )

        if end >= len(tokens):
            break

        start = max(start + 1, end - overlap)

    return chunks

