# RAG Document Cleaning Pipeline

## 1. Overview

Raw documents used in a Retrieval-Augmented Generation (RAG) system often contain noise, including repeated page headers, footers, navigation text, broken line wraps, inconsistent whitespace, and encoding artifacts. These issues can reduce retrieval quality by causing the embedding model to focus on irrelevant content.

This task implements a reusable text-cleaning pipeline that processes every document in the corpus consistently before embedding and indexing.

## 2. Objectives

- Remove repeated headers, footers, page numbers, and known boilerplate.
- Normalize Unicode text using NFKC normalization.
- Fix common whitespace and line-break inconsistencies.
- Apply the same cleaning rules to every document.
- Preserve meaningful content, punctuation, and paragraph boundaries.
- Save before-and-after examples and sample cleaning output.

## 3. Project Structure

```text
project/
├── scripts/
│   └── clean_documents.py
├── data/
│   ├── raw/
│   └── cleaned/
├── docs/
│   └── document_cleaning_pipeline.md
├── results/
│   └── cleaning_samples.json
└── tests/
    └── test_clean_documents.py
```

- `data/raw/` contains the original extracted text files.
- `data/cleaned/` contains cleaned documents ready for downstream processing.
- `scripts/clean_documents.py` implements the reusable cleaning pipeline.
- `results/cleaning_samples.json` stores before-and-after evidence.
- `tests/test_clean_documents.py` verifies the cleaning behavior.

## 4. Cleaning Strategy

### 4.1 Remove boilerplate

Remove known, unwanted text patterns such as:

- `Page 1 of 20`
- `Page 2 of 20`
- Repeated navigation text such as `Home | Products | Contact`
- Known document headers and footers repeated across pages.

Boilerplate removal must use configurable patterns rather than deleting arbitrary lines. A line should only be removed when it matches a known pattern or an explicitly configured boilerplate phrase.

### 4.2 Normalize Unicode and encoding artifacts

Use Python's `unicodedata.normalize("NFKC", text)` to normalize compatible Unicode characters.

This can standardize certain full-width characters and compatibility forms. However, NFKC does not repair every encoding error, such as incorrectly decoded UTF-8 text. Known encoding artifacts should be handled separately when their intended replacements are unambiguous.

### 4.3 Normalize whitespace and line breaks

- Convert Windows and legacy line endings to consistent newlines.
- Remove trailing whitespace from lines.
- Collapse repeated spaces and tabs.
- Repair line wraps when a line clearly continues the previous sentence.
- Preserve paragraph boundaries and meaningful headings.
- Collapse excessive blank lines.

Avoid joining every line blindly, because doing so can destroy lists, headings, and table structures.

## 5. Implementation

Create `scripts/clean_documents.py`:

```python
import re
import unicodedata
from pathlib import Path


# Add only boilerplate patterns appropriate for your corpus.
BOILERPLATE_PATTERNS = [
    re.compile(
        r"^\s*Page\s+\d+\s+of\s+\d+\s*$",
        re.IGNORECASE,
    ),
    re.compile(
        r"^\s*Home\s*\|\s*Products\s*\|\s*Contact\s*$",
        re.IGNORECASE,
    ),
]

# Configure exact phrases that should be removed when present
# as standalone lines.
BOILERPLATE_LINES = {
    "confidential internal document",
}


def remove_boilerplate(text: str) -> str:
    """Remove known page markers and configured boilerplate lines."""
    cleaned_lines = []

    for line in text.splitlines():
        stripped = line.strip()

        if any(pattern.fullmatch(stripped)
               for pattern in BOILERPLATE_PATTERNS):
            continue

        if stripped.casefold() in BOILERPLATE_LINES:
            continue

        cleaned_lines.append(line)

    return "\n".join(cleaned_lines)


def normalize_whitespace(text: str) -> str:
    """Normalize spaces, line endings, and excessive blank lines."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    normalized_lines = [
        re.sub(r"[ \t]+", " ", line).strip()
        for line in text.split("\n")
    ]

    text = "\n".join(normalized_lines)

    # Remove spaces around line breaks and collapse excessive blanks.
    text = re.sub(r"\n[ \t]+\n", "\n\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def repair_line_wraps(text: str) -> str:
    """Join ordinary wrapped prose without merging headings or lists."""
    lines = text.splitlines()
    result = []

    for line in lines:
        line = line.strip()

        if not line:
            if result and result[-1] != "":
                result.append("")
            continue

        is_structural = (
            line.startswith(("#", "-", "*", "•"))
            or bool(re.match(r"^\d+[.)]\s", line))
            or bool(re.match(r"^[A-Z][A-Z0-9\s:]{2,}$", line))
        )

        if (
            result
            and result[-1]
            and not is_structural
            and not result[-1].startswith(("#", "-", "*", "•"))
            and not re.match(r"^\d+[.)]\s", result[-1])
        ):
            result[-1] += " " + line
        else:
            result.append(line)

    return "\n".join(result)


def clean_text(text: str) -> str:
    """Apply the same cleaning sequence to every document."""
    if not isinstance(text, str):
        raise TypeError("Document content must be a string.")

    text = unicodedata.normalize("NFKC", text)
    text = remove_boilerplate(text)
    text = repair_line_wraps(text)
    text = normalize_whitespace(text)

    return text


def clean_corpus(input_dir: str, output_dir: str) -> None:
    """Clean every UTF-8 text document in the input directory."""
    source = Path(input_dir)
    destination = Path(output_dir)

    if not source.is_dir():
        raise FileNotFoundError(
            f"Input directory does not exist: {source}"
        )

    destination.mkdir(parents=True, exist_ok=True)

    for input_file in sorted(source.rglob("*.txt")):
        relative_path = input_file.relative_to(source)
        output_file = destination / relative_path
        output_file.parent.mkdir(parents=True, exist_ok=True)

        raw_text = input_file.read_text(encoding="utf-8")
        cleaned_text = clean_text(raw_text)

        output_file.write_text(
            cleaned_text + "\n",
            encoding="utf-8",
        )

        print(f"Cleaned: {relative_path}")


if __name__ == "__main__":
    clean_corpus("data/raw", "data/cleaned")
```

### Implementation notes

- The script recursively processes `.txt` files in the raw corpus.
- The same `clean_text()` function is applied to every document.
- Relative directory structures are preserved in the output.
- The raw input documents remain unchanged.
- The configured boilerplate patterns should be adapted to the actual source documents.
- The script expects UTF-8 input. If source files use other encodings, detect or configure their encoding explicitly instead of silently ignoring decoding errors.
- Review line-wrap behavior against representative documents before using it for headings, code blocks, or structured tables.

## 6. Before-and-After Evidence

Use the following sample to demonstrate the pipeline's behavior.

### Before cleaning

```text
Home | Products | Contact
Page 1 of 20

Retrieval Augmented Generation
is a technique that combines
document retrieval with language models.


Confidential Internal Document
Page 2 of 20
```

### After cleaning

```text
Retrieval Augmented Generation is a technique that combines document retrieval with language models.
```

### Changes demonstrated

| Issue | Cleaning result |
|---|---|
| Navigation boilerplate | Removed |
| Page markers | Removed |
| Repeated internal notice | Removed using the configured phrase |
| Broken prose line wraps | Joined into a continuous sentence |
| Excessive blank lines | Collapsed |
| Original raw file | Preserved |

The exact output depends on the configured patterns and the line structure of the input. Boilerplate should be removed only when it is known to be irrelevant.

## 7. Sample Output Artifact

Save the following evidence in `results/cleaning_samples.json`:

```json
[
  {
    "document": "sample_001.txt",
    "before": "Home | Products | Contact\nPage 1 of 20\n\nRetrieval Augmented Generation\nis a technique that combines\ndocument retrieval with language models.\n\n\nConfidential Internal Document\nPage 2 of 20",
    "after": "Retrieval Augmented Generation is a technique that combines document retrieval with language models.",
    "checks": {
      "navigation_removed": true,
      "page_markers_removed": true,
      "line_wraps_repaired": true,
      "excessive_blank_lines_removed": true
    }
  }
]
```

This artifact records a reproducible example of the cleaning pipeline's expected behavior.

## 8. Testing

Create `tests/test_clean_documents.py`:

```python
import unicodedata

from scripts.clean_documents import clean_text


def test_removes_page_markers_and_navigation():
    raw = (
        "Home | Products | Contact\n"
        "Page 1 of 20\n"
        "Useful document content."
    )

    result = clean_text(raw)

    assert "Page 1 of 20" not in result
    assert "Home | Products | Contact" not in result
    assert "Useful document content." in result


def test_repairs_wrapped_prose():
    raw = (
        "Retrieval Augmented Generation\n"
        "combines retrieval with generation."
    )

    result = clean_text(raw)

    assert result == (
        "Retrieval Augmented Generation combines "
        "retrieval with generation."
    )


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
```

Run the tests from the project root:

```bash
python -m pytest tests/test_clean_documents.py -v
```

Run the cleaning pipeline:

```bash
python scripts/clean_documents.py
```

## 9. Integration with the RAG Pipeline

Run document cleaning after text extraction and before chunking, embedding, and indexing.

Recommended processing sequence:

1. Extract text from source documents.
2. Apply `clean_text()` to every document.
3. Save cleaned documents for inspection and reuse.
4. Split cleaned content into retrieval chunks.
5. Generate embeddings from the cleaned chunks.
6. Index embeddings in the vector database.

This ensures the same cleaning logic is applied consistently before retrieval indexing.

## 10. Acceptance Criteria

- [ ] Known repeated headers, footers, and page markers are removed.
- [ ] Unicode text is normalized using NFKC.
- [ ] Repeated spaces and excessive blank lines are normalized.
- [ ] Ordinary wrapped prose is repaired without indiscriminately merging paragraphs.
- [ ] Every `.txt` document is processed with the same cleaning function.
- [ ] Raw documents are preserved.
- [ ] Cleaned output is written to the designated directory.
- [ ] Before-and-after samples demonstrate the effect of cleaning.
- [ ] Automated tests cover boilerplate, whitespace, line wraps, Unicode, and paragraph preservation.
- [ ] The pipeline and sample output are committed to Git.

## 11. Git Workflow

Create and switch to the feature branch:

```bash
git checkout -b feature/rag-document-cleaning-pipeline
```

Stage the implementation, documentation, sample output, and tests:



## 12. Expected Outcome

The project now has a reusable cleaning pipeline that produces consistent, retrieval-ready text across the document corpus. Known boilerplate and common formatting noise are removed, Unicode and whitespace are normalized, and before-and-after evidence demonstrates the transformation. The cleaned documents can then be passed to the RAG chunking, embedding, and indexing stages.