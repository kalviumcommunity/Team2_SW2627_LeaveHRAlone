import unicodedata
import pytest
from app.rag.processing.cleaner import clean_text


def test_removes_page_markers_and_navigation():
    raw = (
        "Home | Products | Contact\n"
        "Page 1 of 20\n"
        "Useful company policy content."
    )
    result = clean_text(raw)
    assert "Page 1 of 20" not in result
    assert "Home | Products | Contact" not in result
    assert "Useful company policy content." in result


def test_repairs_wrapped_prose():
    raw = (
        "Retrieval Augmented Generation\n"
        "combines retrieval with generation."
    )
    result = clean_text(raw)
    assert result == "Retrieval Augmented Generation combines retrieval with generation."


def test_normalizes_unicode():
    raw = "ＡＩ ＲＡＧ"
    result = clean_text(raw)
    assert result == unicodedata.normalize("NFKC", raw)


def test_collapses_excessive_blank_lines():
    raw = "First paragraph.\n\n\n\nSecond paragraph."
    result = clean_text(raw)
    assert result == "First paragraph.\n\nSecond paragraph."


def test_preserves_paragraph_boundaries():
    raw = "First paragraph.\n\nSecond paragraph."
    result = clean_text(raw)
    assert result == raw


def test_preserves_markdown_structural_elements():
    raw = (
        "# Leave Policy\n"
        "- Point 1\n"
        "- Point 2\n"
        "1. Ordered item\n"
    )
    result = clean_text(raw)
    assert "# Leave Policy" in result
    assert "- Point 1" in result
    assert "1. Ordered item" in result
