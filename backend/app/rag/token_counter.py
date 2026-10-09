"""
LeaveHRAlone (PolicyPilot AI) - Token Counter & Cost Estimation Script

This script:
1. Uses tiktoken to count tokens for sample inputs/outputs from the project corpus.
2. Reports token counts for three samples of varying length (short query, paragraph, full PRD doc).
3. Estimates operational costs under different LLM pricing tiers (GPT-4o, GPT-4o-mini, Claude 3.5 Sonnet).
4. Demonstrates the non-linear relationship between text length (chars/words) and token count.
5. Saves clean sample results for audit and PR review.
"""

import os
import json
from typing import Dict, Any, List
import tiktoken

# Pricing tiers in USD per 1,000,000 tokens ($/1M tokens)
PRICING_MODELS = {
    "gpt-4o": {
        "input_cost_per_1m": 2.50,
        "output_cost_per_1m": 10.00,
        "description": "OpenAI GPT-4o (Default RAG Generator)"
    },
    "gpt-4o-mini": {
        "input_cost_per_1m": 0.15,
        "output_cost_per_1m": 0.60,
        "description": "OpenAI GPT-4o-mini (Cost-Optimized RAG)"
    },
    "claude-3-5-sonnet": {
        "input_cost_per_1m": 3.00,
        "output_cost_per_1m": 15.00,
        "description": "Anthropic Claude 3.5 Sonnet"
    },
    "text-embedding-3-small": {
        "input_cost_per_1m": 0.02,
        "output_cost_per_1m": 0.00,
        "description": "OpenAI Text Embedding 3 Small (Vector Database Indexing)"
    }
}


def get_encoder(model_name: str = "gpt-4o") -> tiktoken.Encoding:
    """Returns tiktoken encoding for specified model, defaulting to cl100k_base / o200k_base."""
    try:
        return tiktoken.encoding_for_model(model_name)
    except KeyError:
        return tiktoken.get_encoding("cl100k_base")


def count_tokens(text: str, encoder: tiktoken.Encoding = None) -> int:
    """Calculates exact token count for a text string."""
    if encoder is None:
        encoder = get_encoder()
    return len(encoder.encode(text))


def calculate_cost(input_tokens: int, output_tokens: int, model_key: str = "gpt-4o") -> Dict[str, Any]:
    """Calculates input, output, and total cost based on model pricing rates."""
    rates = PRICING_MODELS[model_key]
    input_cost = (input_tokens / 1_000_000) * rates["input_cost_per_1m"]
    output_cost = (output_tokens / 1_000_000) * rates["output_cost_per_1m"]
    total_cost = input_cost + output_cost

    return {
        "model": model_key,
        "description": rates["description"],
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens,
        "input_cost_usd": round(input_cost, 6),
        "output_cost_usd": round(output_cost, 6),
        "total_cost_usd": round(total_cost, 6)
    }


def load_prd_sample(prd_path: str = "PRD.md") -> str:
    """Loads text content from project PRD.md."""
    if os.path.exists(prd_path):
        with open(prd_path, "r", encoding="utf-8") as f:
            return f.read()
    return "PolicyPilot AI is an AI-powered HR assistant that allows employees to ask questions about company policies."


def run_token_analysis() -> Dict[str, Any]:
    """Executes full token analysis across tasks and returns structured dictionary."""
    encoder = get_encoder("gpt-4o")

    # Task 2 Samples
    sample_1_query = "How many paid annual leaves am I entitled to in India per calendar year?"
    
    sample_2_paragraph = (
        "Employees in India are entitled to 24 paid annual leaves per calendar year, accrued monthly at the rate of "
        "2 days per completed month of service. Unused annual leaves up to a maximum limit of 10 days may be carried "
        "forward to the subsequent calendar year. Any additional unused leave beyond 10 days shall expire on December 31st "
        "unless prior written approval is granted by the HR Director. Leave requests exceeding 3 consecutive business days "
        "must be submitted in the HR portal at least 14 days in advance."
    )

    full_prd_text = load_prd_sample()

    # Task 2 Counts
    count_1 = count_tokens(sample_1_query, encoder)
    count_2 = count_tokens(sample_2_paragraph, encoder)
    count_3 = count_tokens(full_prd_text, encoder)

    task_2_results = [
        {
            "sample_name": "Sample 1: Short Employee Query",
            "character_count": len(sample_1_query),
            "word_count": len(sample_1_query.split()),
            "token_count": count_1,
            "text_preview": sample_1_query
        },
        {
            "sample_name": "Sample 2: HR Policy Section / Paragraph",
            "character_count": len(sample_2_paragraph),
            "word_count": len(sample_2_paragraph.split()),
            "token_count": count_2,
            "text_preview": sample_2_paragraph[:120] + "..."
        },
        {
            "sample_name": "Sample 3: Full PRD Document (Project Corpus)",
            "character_count": len(full_prd_text),
            "word_count": len(full_prd_text.split()),
            "token_count": count_3,
            "text_preview": full_prd_text[:120] + "..."
        }
    ]

    # Task 3 Cost Estimates
    # Scenario A: Single Query (Input: Query + Retrieved Chunks = ~1,500 tokens; Output: ~250 tokens)
    single_query_input = count_1 + count_2 + 1000  # Query + RAG chunks
    single_query_output = 250  # Generated LLM answer with citations

    cost_estimates_single = {
        model_key: calculate_cost(single_query_input, single_query_output, model_key)
        for model_key in PRICING_MODELS if "embedding" not in model_key
    }

    # Scenario B: Scale Estimate (10,000 Monthly Employee Queries)
    scale_queries = 10_000
    total_scale_input = single_query_input * scale_queries
    total_scale_output = single_query_output * scale_queries

    cost_estimates_scale = {
        model_key: calculate_cost(total_scale_input, total_scale_output, model_key)
        for model_key in PRICING_MODELS if "embedding" not in model_key
    }

    # Scenario C: Knowledge Base Vector Indexing Cost (50 HR Documents = ~500,000 tokens)
    embedding_cost = calculate_cost(500_000, 0, "text-embedding-3-small")

    # Task 4 Length-Token Relationship Analysis
    comparison_samples = [
        {
            "label": "Plain English Text",
            "text": "Employees can request remote work approval up to two days per week with manager consent."
        },
        {
            "label": "Structured Code / JSON Payload",
            "text": '{"user_id": "usr_9981", "region": "India", "roles": ["EMPLOYEE", "HR_ADMIN"], "metadata": {"active": true}}'
        },
        {
            "label": "Technical & Legal Policy Clauses",
            "text": "Sub-clause (iv)(b): Under Sec 4.2.1(B)-2026, non-exempt FTEs receiving $75,000.00/yr must comply with Rule #109-A."
        },
        {
            "label": "Non-English / Multilingual Text (Hindi)",
            "text": "कर्मचारी प्रत्येक कैलेंडर वर्ष में 24 वैतनिक वार्षिक छुट्टियों के हकदार हैं।"
        }
    ]

    task_4_results = []
    for item in comparison_samples:
        t = item["text"]
        chars = len(t)
        words = len(t.split())
        tokens = count_tokens(t, encoder)
        chars_per_token = round(chars / tokens, 2) if tokens > 0 else 0
        tokens_per_word = round(tokens / words, 2) if words > 0 else 0

        task_4_results.append({
            "category": item["label"],
            "sample_text": t,
            "character_count": chars,
            "word_count": words,
            "token_count": tokens,
            "chars_per_token": chars_per_token,
            "tokens_per_word": tokens_per_word
        })

    full_results = {
        "project": "LeaveHRAlone (PolicyPilot AI)",
        "encoder": encoder.name if hasattr(encoder, "name") else "o200k_base / cl100k_base",
        "task_2_sample_counts": task_2_results,
        "task_3_cost_estimation": {
            "single_query_simulation": {
                "input_tokens": single_query_input,
                "output_tokens": single_query_output,
                "model_costs": cost_estimates_single
            },
            "scale_10k_monthly_queries": {
                "total_input_tokens": total_scale_input,
                "total_output_tokens": total_scale_output,
                "model_costs": cost_estimates_scale
            },
            "vector_embedding_indexing": embedding_cost
        },
        "task_4_length_token_relationship": task_4_results
    }

    return full_results


def print_report(results: Dict[str, Any]) -> None:
    """Prints a formatted report to the console."""
    print("=" * 80)
    print("      LEAVEHRALONE (POLICYPILOT AI) - TOKEN & COST ANALYSIS REPORT      ")
    print("=" * 80)
    print(f"Tokenizer Encoder: {results['encoder']}\n")

    print("--------------------------------------------------------------------------------")
    print("TASK 2: TOKEN COUNTS FOR THREE SAMPLES OF VARYING LENGTH")
    print("--------------------------------------------------------------------------------")
    for s in results["task_2_sample_counts"]:
        print(f"• {s['sample_name']}:")
        print(f"  - Characters: {s['character_count']:,}")
        print(f"  - Words:      {s['word_count']:,}")
        print(f"  - Tokens:     {s['token_count']:,}")
        print(f"  - Preview:    \"{s['text_preview']}\"\n")

    print("--------------------------------------------------------------------------------")
    print("TASK 3: COST ESTIMATES FROM TOKEN COUNTS")
    print("--------------------------------------------------------------------------------")
    sq = results["task_3_cost_estimation"]["single_query_simulation"]
    print(f"Single Query RAG Simulation (Input: {sq['input_tokens']:,} tokens, Output: {sq['output_tokens']:,} tokens):")
    for m, details in sq["model_costs"].items():
        print(f"  • {m:18s}: ${details['total_cost_usd']:.6f} per query ({details['description']})")

    sc = results["task_3_cost_estimation"]["scale_10k_monthly_queries"]
    print(f"\nMonthly Operational Scale (10,000 Queries | Input: {sc['total_input_tokens']:,} tokens, Output: {sc['total_output_tokens']:,} tokens):")
    for m, details in sc["model_costs"].items():
        print(f"  • {m:18s}: ${details['total_cost_usd']:>8.2f} / month")

    emb = results["task_3_cost_estimation"]["vector_embedding_indexing"]
    print(f"\nVector Embedding Indexing (50 HR Docs / 500k tokens using {emb['model']}):")
    print(f"  • One-Time Indexing Cost: ${emb['total_cost_usd']:.4f}\n")

    print("--------------------------------------------------------------------------------")
    print("TASK 4: DEMONSTRATING LENGTH-TOKEN RELATIONSHIP & NON-PROPORTIONALITY")
    print("--------------------------------------------------------------------------------")
    print(f"{'Category':<32} | {'Chars':<6} | {'Words':<6} | {'Tokens':<6} | {'Chars/Tok':<9} | {'Tok/Word':<8}")
    print("-" * 80)
    for r in results["task_4_length_token_relationship"]:
        print(f"{r['category']:<32} | {r['character_count']:<6} | {r['word_count']:<6} | {r['token_count']:<6} | {r['chars_per_token']:<9.2f} | {r['tokens_per_word']:<8.2f}")
    print("\nKey Insight:")
    print("• Plain English averages ~4 chars/token (~1.25 tokens/word).")
    print("• Code/JSON & Legal punctuation break into individual sub-tokens (higher tokens/word ratio).")
    print("• Multilingual/non-ASCII text requires multiple bytes per token, resulting in significantly higher token density.\n")
    print("=" * 80)


def generate_markdown_report(results: Dict[str, Any], output_md_path: str = "docs/TOKEN_COST_ANALYSIS.md") -> None:
    """Generates a Markdown documentation artifact summarizing the token and cost analysis."""
    sq = results["task_3_cost_estimation"]["single_query_simulation"]
    sc = results["task_3_cost_estimation"]["scale_10k_monthly_queries"]
    emb = results["task_3_cost_estimation"]["vector_embedding_indexing"]

    md_content = f"""# Token Counting & Cost Estimation Analysis

> **Project**: LeaveHRAlone (PolicyPilot AI)  
> **Encoder**: `{results['encoder']}`  
> **Date**: October 2026  

---

## 1. Executive Summary

In a Retrieval-Augmented Generation (RAG) architecture, every query sends both user prompts and retrieved document chunks to an LLM. Because providers charge separately per **input token** and **output token**, understanding token density and operational cost is critical before scaling vector retrieval and chunking parameters.

This report documents token counts across representative samples, provides multi-tier cost projections, and demonstrates why character length and token count track together generally but diverge on structured code and non-English text.

---

## 2. Token Counts Across Sample Inputs (Task 2)

| Sample Name | Character Count | Word Count | Token Count | Avg Chars/Token |
| --- | --- | --- | --- | --- |
"""
    for s in results["task_2_sample_counts"]:
        c_tok = round(s["character_count"] / s["token_count"], 2) if s["token_count"] > 0 else 0
        md_content += f"| **{s['sample_name']}** | {s['character_count']:,} | {s['word_count']:,} | **{s['token_count']:,}** | {c_tok} |\n"

    md_content += f"""
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
- **Context Payload**: {sq['input_tokens']:,} input tokens (User query + Top-5 retrieved chunks)
- **Response Length**: {sq['output_tokens']:,} output tokens (Grounded answer + source citations)

| LLM Model | Input Cost ($) | Output Cost ($) | Total Cost per Query ($) |
| --- | --- | --- | --- |
"""
    for m, details in sq["model_costs"].items():
        md_content += f"| `{m}` | ${details['input_cost_usd']:.6f} | ${details['output_cost_usd']:.6f} | **${details['total_cost_usd']:.6f}** |\n"

    md_content += f"""
### Operational Scale Projection (10,000 Monthly Queries)
- **Total Monthly Input**: {sc['total_input_tokens']:,} tokens
- **Total Monthly Output**: {sc['total_output_tokens']:,} tokens

| LLM Model | Monthly Input Cost ($) | Monthly Output Cost ($) | Total Monthly Cost ($) |
| --- | --- | --- | --- |
"""
    for m, details in sc["model_costs"].items():
        md_content += f"| `{m}` | ${details['input_cost_usd']:.2f} | ${details['output_cost_usd']:.2f} | **${details['total_cost_usd']:.2f}** |\n"

    md_content += f"""
### Vector Database Indexing Cost
- **Corpus Size**: 50 HR documents (~500,000 tokens)
- **Embedding Model**: `text-embedding-3-small` ($0.02 / 1M tokens)
- **One-Time Indexing Cost**: **${emb['total_cost_usd']:.4f}**

---

## 4. Length vs Token Count Relationship (Task 4)

While character count and token count track together in plain English prose, they are **not strictly proportional**. Structural syntax, special characters, long technical terms, and non-ASCII languages alter token density.

| Text Category | Characters | Words | Tokens | Chars / Token | Tokens / Word |
| --- | --- | --- | --- | --- | --- |
"""
    for r in results["task_4_length_token_relationship"]:
        md_content += f"| **{r['category']}** | {r['character_count']} | {r['word_count']} | **{r['token_count']}** | {r['chars_per_token']} | {r['tokens_per_word']} |\n"

    md_content += """
### Key Observations & Takeaways
1. **Plain English Prose**: Averages **~4 characters per token** (~1.2 - 1.3 tokens per word).
2. **Structured Code & JSON**: Syntax characters (`{`, `}`, `"`, `:`, `[`, `]`) often tokenize into individual 1-character tokens. Words with underscores or camelCase split into multiple tokens, lowering `chars/token` to ~2.8 - 3.2.
3. **Technical Legal Clauses**: Punctuation (`Sec 4.2.1(B)-2026`), dollar signs, and mixed numbers increase token counts compared to standard prose.
4. **Multilingual Text (Non-ASCII)**: UTF-8 characters outside the Latin alphabet (e.g. Hindi Devanagari script) split into multi-token byte sequences. The same semantic sentence uses ~2.5x more tokens in Hindi than in English.

---
"""

    os.makedirs(os.path.dirname(output_md_path), exist_ok=True)
    with open(output_md_path, "w", encoding="utf-8") as f:
        f.write(md_content)
    print(f"Saved Markdown report to: {output_md_path}")


def main():
    results = run_token_analysis()
    print_report(results)

    # Save JSON results
    json_path = "backend/app/rag/token_cost_results.json"
    os.makedirs(os.path.dirname(json_path), exist_ok=True)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"Saved JSON results to: {json_path}")

    # Generate Markdown documentation report
    generate_markdown_report(results, "docs/TOKEN_COST_ANALYSIS.md")


if __name__ == "__main__":
    main()
