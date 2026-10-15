# Token-Aware Chunking for RAG

## 1. Overview

In a Retrieval-Augmented Generation (RAG) system, document chunking determines how extracted content is divided before embedding and indexing. Character-based splitting does not guarantee a consistent token count, which can lead to oversized chunks, inefficient embedding costs, and incomplete context at chunk boundaries.

This task implements a token-aware chunking pipeline using `tiktoken`. It measures chunk sizes in tokens, adds controlled overlap between adjacent chunks, and produces sample output to demonstrate how overlap preserves context.

## 2. Objectives

- Measure document and chunk sizes using a tokenizer rather than character counts.
- Configure a maximum chunk size in tokens.
- Add a configurable overlap between adjacent chunks.
- Preserve context across chunk boundaries.
- Demonstrate chunking behavior with and without overlap.
- Document the reasoning behind the selected chunk size and overlap.
- Commit the implementation, tests, and sample output.

## 3. Technology Stack

- **Python:** Chunking implementation.
- **tiktoken:** Token counting and token-based splitting.
- **pytest:** Automated tests.
- **JSON:** Sample chunk output and metadata.

Install the dependencies:

```bash
pip install tiktoken pytest
```

## 4. Chunking Configuration

Use the following initial settings for a general-purpose RAG pipeline:

| Parameter | Value | Reason |
|---|---:|---|
| Chunk size | 500 tokens | Provides enough context for many factual passages without making chunks excessively large |
| Chunk overlap | 75 tokens | Preserves context across boundaries while limiting duplicated content |
| Tokenizer | `cl100k_base` | Suitable for models and embedding workflows that use this encoding |
| Maximum chunk size | 500 tokens | Prevents generated chunks from exceeding the configured token budget |

**Model compatibility:** `cl100k_base` is a reasonable starting point for compatible OpenAI models, but it is not universal. Select the tokenizer that matches your embedding or generation model where possible. For example, models using a different tokenizer require a corresponding encoding or tokenizer library.

### Why 500 tokens and 75 tokens of overlap?

A 500-token chunk provides a practical starting point for retrieval tasks involving technical documentation, explanations, and general knowledge. The 75-token overlap is 15% of the chunk size, allowing adjacent chunks to share a short section of context.

These are initial tuning values, not universal optimal settings. Evaluate them against your document corpus, retrieval quality, latency, and embedding costs.

The chunk size must also fit within the overall model context window alongside the user's question, retrieved passages, system instructions, and generated answer. A 500-token chunk alone does not guarantee that an entire RAG prompt fits the context window.

## 5. Project Structure

```text
project/
├── scripts/
│   └── token_chunker.py
├── docs/
│   └── token_aware_chunking.md
├── results/
│   └── chunking_samples.json
└── tests/
    └── test_token_chunker.py
```

## 6. Implementation

Create `scripts/token_chunker.py`:

```python
import json
from pathlib import Path

import tiktoken


CHUNK_SIZE = 500
CHUNK_OVERLAP = 75
TOKENIZER_NAME = "cl100k_base"


def get_tokenizer(encoding_name=TOKENIZER_NAME):
    """Return the configured tokenizer."""
    return tiktoken.get_encoding(encoding_name)


def count_tokens(text, tokenizer=None):
    """Count tokens using the configured encoding."""
    tokenizer = tokenizer or get_tokenizer()
    return len(tokenizer.encode(text))


def chunk_text(
    text,
    chunk_size=CHUNK_SIZE,
    overlap=CHUNK_OVERLAP,
    tokenizer=None,
):
    """Split text into token-bounded chunks with controlled overlap."""
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than zero.")

    if overlap < 0:
        raise ValueError("overlap cannot be negative.")

    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size.")

    tokenizer = tokenizer or get_tokenizer()
    tokens = tokenizer.encode(text)

    if not tokens:
        return []

    chunks = []
    start = 0

    while start < len(tokens):
        end = min(start + chunk_size, len(tokens))
        chunk_tokens = tokens[start:end]

        chunks.append({
            "chunk_id": len(chunks),
            "text": tokenizer.decode(chunk_tokens),
            "start_token": start,
            "end_token": end,
            "token_count": len(chunk_tokens),
        })

        if end == len(tokens):
            break

        start = end - overlap

    return chunks


def save_chunks(chunks, output_path):
    """Save chunks and metadata as JSON."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(chunks, file, indent=2, ensure_ascii=False)


def main():
    input_path = Path("data/raw/document.txt")
    output_path = Path("results/chunking_samples.json")

    if not input_path.exists():
        raise FileNotFoundError(
            f"Input document not found: {input_path}"
        )

    text = input_path.read_text(encoding="utf-8")
    chunks = chunk_text(text)

    save_chunks(chunks, output_path)

    print(f"Total document tokens: {count_tokens(text)}")
    print(f"Total chunks: {len(chunks)}")

    for chunk in chunks:
        print(
            f"Chunk {chunk['chunk_id']}: "
            f"{chunk['token_count']} tokens"
        )


if __name__ == "__main__":
    main()
```

### How the algorithm works

1. The tokenizer converts the input document into token IDs.
2. The algorithm takes up to 500 tokens for the first chunk.
3. The next chunk starts 75 tokens before the previous chunk's end.
4. The process repeats until all tokens are covered.
5. Each chunk includes its text, token count, and token boundaries.

For adjacent full chunks, the overlap is exactly 75 tokens. The final chunk can be shorter than the configured maximum.

## 7. Demonstrating Boundary Context Preservation

Consider the following passage:

> A deployment should be rolled back when the error rate exceeds the defined threshold. The monitoring service evaluates the error rate over a five-minute window. If the threshold is exceeded for two consecutive evaluations, the release controller initiates a rollback and records the incident.

Suppose the sentence explaining the rollback condition falls across a chunk boundary.

### Without overlap

<text color="secondary" size="sm">Illustrative boundary split</text>

<box border radius="lg" padding={3} gap={2}>
  <box background="surface-secondary" radius="md" padding={3} gap={1}>
    **Chunk 1**

    A deployment should be rolled back when the error rate exceeds the defined threshold. The monitoring service evaluates the error rate over a five-minute window. If the threshold is exceeded for two consecutive evaluations...
  </box>
  <box background="surface-secondary" radius="md" padding={3} gap={1}>
    **Chunk 2**

    ...the release controller initiates a rollback and records the incident.
  </box>
</box>

The second chunk begins with a fragment that depends on the previous chunk. A retrieval system returning only the second chunk may lose the condition that triggers the rollback.

### With overlap

<box border radius="lg" padding={3} gap={2}>
  <box background="surface-secondary" radius="md" padding={3} gap={1}>
    **Chunk 1**

    A deployment should be rolled back when the error rate exceeds the defined threshold. The monitoring service evaluates the error rate over a five-minute window. If the threshold is exceeded for two consecutive evaluations, the release controller initiates a rollback and records the incident.
  </box>
  <box background="surface-secondary" radius="md" padding={3} gap={1}>
    **Chunk 2**

    The monitoring service evaluates the error rate over a five-minute window. If the threshold is exceeded for two consecutive evaluations, the release controller initiates a rollback and records the incident.
  </box>
</box>

The overlapping text allows the second chunk to retain context about the monitoring window and the triggering condition.

*Note: These snippets illustrate the concept; they are not measured output from the implementation. The actual chunk boundary depends on the selected tokenizer and token budget.*

## 8. Sample Output

Save actual execution results in `results/chunking_samples.json`.

An illustrative example of the output structure is:

```json
{
  "configuration": {
    "tokenizer": "cl100k_base",
    "chunk_size": 500,
    "overlap": 75
  },
  "total_document_tokens": 1120,
  "total_chunks": 3,
  "chunks": [
    {
      "chunk_id": 0,
      "start_token": 0,
      "end_token": 500,
      "token_count": 500,
      "text": "First chunk text..."
    },
    {
      "chunk_id": 1,
      "start_token": 425,
      "end_token": 925,
      "token_count": 500,
      "text": "Second chunk text..."
    },
    {
      "chunk_id": 2,
      "start_token": 850,
      "end_token": 1120,
      "token_count": 270,
      "text": "Final chunk text..."
    }
  ]
}
```

The token counts and text above are illustrative. Run the script against your actual input to generate verified chunk counts and example chunks. In the implementation, `save_chunks()` currently saves the list of chunk objects; if you want the complete configuration and summary in the same JSON file, wrap the chunks and metadata in a single dictionary before saving.

## 9. Automated Tests

Create `tests/test_token_chunker.py`:

```python
import tiktoken
import pytest

from scripts.token_chunker import chunk_text, count_tokens


def test_chunks_respect_token_limit():
    tokenizer = tiktoken.get_encoding("cl100k_base")
    text = "deployment monitoring rollback " * 300

    chunks = chunk_text(
        text,
        chunk_size=100,
        overlap=20,
        tokenizer=tokenizer,
    )

    assert chunks
    assert all(
        chunk["token_count"] <= 100
        for chunk in chunks
    )


def test_adjacent_chunks_have_exact_overlap():
    tokenizer = tiktoken.get_encoding("cl100k_base")
    text = "alpha beta gamma delta " * 100

    chunks = chunk_text(
        text,
        chunk_size=50,
        overlap=10,
        tokenizer=tokenizer,
    )

    for previous, current in zip(chunks, chunks[1:]):
        assert current["start_token"] == (
            previous["end_token"] - 10
        )


def test_empty_text_returns_no_chunks():
    assert chunk_text("") == []


def test_invalid_chunk_size_is_rejected():
    with pytest.raises(ValueError):
        chunk_text("example text", chunk_size=0, overlap=0)


def test_overlap_must_be_smaller_than_chunk_size():
    with pytest.raises(ValueError):
        chunk_text("example text", chunk_size=10, overlap=10)


def test_token_count_uses_tokenizer():
    tokenizer = tiktoken.get_encoding("cl100k_base")

    assert count_tokens("Hello world", tokenizer) == len(
        tokenizer.encode("Hello world")
    )
```

Run the tests:

```bash
python -m pytest tests/test_token_chunker.py -v
```

## 10. Running the Pipeline

Place an extracted text document at `data/raw/document.txt`.

Run:

```bash
python scripts/token_chunker.py
```

The script prints the document's token count, total number of chunks, and token count of each chunk. It saves the generated chunk records to `results/chunking_samples.json`.

## 11. Acceptance Criteria

- [ ] Chunk size is measured in tokens using `tiktoken`.
- [ ] Chunk size and overlap are configurable.
- [ ] Overlap repeats the last N tokens of the preceding chunk.
- [ ] Invalid chunk configurations are rejected.
- [ ] Every chunk stays within the configured token limit.
- [ ] A boundary example demonstrates the value of overlap.
- [ ] Chunk size and overlap are justified for the selected model and workload.
- [ ] Sample output includes chunk counts, token boundaries, and example text.
- [ ] Tests cover token limits, overlap, empty input, and invalid configuration.
- [ ] Code, tests, documentation, and sample output are committed.



## 13. Expected Outcome

The RAG pipeline now has a reusable token-aware chunker that enforces a configurable token budget and controlled overlap. Chunk metadata supports verification and debugging, while the sample output and tests demonstrate the behavior required for reliable downstream embedding and retrieval.