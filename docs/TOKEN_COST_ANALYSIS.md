# Token Counting & Cost Estimation Analysis

> **Project**: LeaveHRAlone (PolicyPilot AI)  
> **Encoder**: `o200k_base`  
> **Date**: October 2026  

---

## 1. Executive Summary

In a Retrieval-Augmented Generation (RAG) architecture, every query sends both user prompts and retrieved document chunks to an LLM. Because providers charge separately per **input token** and **output token**, understanding token density and operational cost is critical before scaling vector retrieval and chunking parameters.

This report documents token counts across representative samples, provides multi-tier cost projections, and demonstrates why character length and token count track together generally but diverge on structured code and non-English text.

---

## 2. Token Counts Across Sample Inputs (Task 2)

| Sample Name | Character Count | Word Count | Token Count | Avg Chars/Token |
| --- | --- | --- | --- | --- |
| **Sample 1: Short Employee Query** | 72 | 14 | **15** | 4.8 |
| **Sample 2: HR Policy Section / Paragraph** | 506 | 88 | **102** | 4.96 |
| **Sample 3: Full PRD Document (Project Corpus)** | 21,345 | 2,684 | **4,404** | 4.85 |

---

## 3. RAG Query Cost Estimation (Task 3)

### Pricing Tiers Reference
| Model | Input Rate ($/1M Tokens) | Output Rate ($/1M Tokens) | Target Use Case |
| --- | --- | --- | --- |
| `gpt-4o` | $2.50 | $10.00 | High-accuracy RAG answer generation |
| `gpt-4o-mini` | $0.15 | $0.60 | Cost-optimized RAG answer generation |
| `claude-3-5-sonnet` | $3.00 | $15.00 | Complex policy reasoning & fallback |
| `text-embedding-3-small` | $0.02 | $0.00 | Vector embedding generation |

### Single Query RAG Cost Breakdown
- **Context Payload**: 1,117 input tokens (User query + Top-5 retrieved chunks)
- **Response Length**: 250 output tokens (Grounded answer + source citations)

| LLM Model | Input Cost ($) | Output Cost ($) | Total Cost per Query ($) |
| --- | --- | --- | --- |
| `gpt-4o` | $0.002792 | $0.002500 | **$0.005293** |
| `gpt-4o-mini` | $0.000168 | $0.000150 | **$0.000318** |
| `claude-3-5-sonnet` | $0.003351 | $0.003750 | **$0.007101** |

### Operational Scale Projection (10,000 Monthly Queries)
- **Total Monthly Input**: 11,170,000 tokens
- **Total Monthly Output**: 2,500,000 tokens

| LLM Model | Monthly Input Cost ($) | Monthly Output Cost ($) | Total Monthly Cost ($) |
| --- | --- | --- | --- |
| `gpt-4o` | $27.93 | $25.00 | **$52.92** |
| `gpt-4o-mini` | $1.68 | $1.50 | **$3.18** |
| `claude-3-5-sonnet` | $33.51 | $37.50 | **$71.01** |

### Vector Database Indexing Cost
- **Corpus Size**: 50 HR documents (~500,000 tokens)
- **Embedding Model**: `text-embedding-3-small` ($0.02 / 1M tokens)
- **One-Time Indexing Cost**: **$0.0100**

---

## 4. Length vs Token Count Relationship (Task 4)

While character count and token count track together in plain English prose, they are **not strictly proportional**. Structural syntax, special characters, long technical terms, and non-ASCII languages alter token density.

| Text Category | Characters | Words | Tokens | Chars / Token | Tokens / Word |
| --- | --- | --- | --- | --- | --- |
| **Plain English Text** | 88 | 15 | **16** | 5.5 | 1.07 |
| **Structured Code / JSON Payload** | 107 | 10 | **35** | 3.06 | 3.5 |
| **Technical & Legal Policy Clauses** | 114 | 14 | **44** | 2.59 | 3.14 |
| **Non-English / Multilingual Text (Hindi)** | 76 | 12 | **26** | 2.92 | 2.17 |

### Key Observations & Takeaways
1. **Plain English Prose**: Averages **~4 characters per token** (~1.2 - 1.3 tokens per word).
2. **Structured Code & JSON**: Syntax characters (`{`, `}`, `"`, `:`, `[`, `]`) often tokenize into individual 1-character tokens. Words with underscores or camelCase split into multiple tokens, lowering `chars/token` to ~2.8 - 3.2.
3. **Technical Legal Clauses**: Punctuation (`Sec 4.2.1(B)-2026`), dollar signs, and mixed numbers increase token counts compared to standard prose.
4. **Multilingual Text (Non-ASCII)**: UTF-8 characters outside the Latin alphabet (e.g. Hindi Devanagari script) split into multi-token byte sequences. The same semantic sentence uses ~2.5x more tokens in Hindi than in English.

---
