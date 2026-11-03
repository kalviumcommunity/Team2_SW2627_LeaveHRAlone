import pytest
import tiktoken
from app.rag.processing.chunker import chunk_text, count_tokens


def test_chunks_respect_token_limit():
    tokenizer = tiktoken.get_encoding("cl100k_base")
    text = "maternity leave policy benefit calculation " * 150

    chunks = chunk_text(
        text,
        chunk_size=100,
        overlap=20,
        tokenizer=tokenizer,
    )
    assert chunks
    assert all(chunk.token_count <= 100 for chunk in chunks)


def test_adjacent_chunks_have_exact_overlap():
    tokenizer = tiktoken.get_encoding("cl100k_base")
    text = "policy rule section paragraph benefit employee " * 60

    chunks = chunk_text(
        text,
        chunk_size=50,
        overlap=10,
        tokenizer=tokenizer,
    )
    assert len(chunks) > 1
    for previous, current in zip(chunks, chunks[1:]):
        assert current.start_token == (previous.end_token - 10)


def test_empty_text_returns_no_chunks():
    assert chunk_text("") == []


def test_invalid_chunk_size_is_rejected():
    with pytest.raises(ValueError):
        chunk_text("sample content", chunk_size=0, overlap=0)


def test_overlap_must_be_smaller_than_chunk_size():
    with pytest.raises(ValueError):
        chunk_text("sample content", chunk_size=50, overlap=50)


def test_count_tokens_utility():
    text = "LeaveHRAlone AI Assistant"
    assert count_tokens(text) > 0
