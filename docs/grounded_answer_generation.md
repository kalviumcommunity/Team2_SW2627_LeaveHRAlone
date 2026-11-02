Grounded Answer Generation
The final step of Retrieval-Augmented Generation (RAG) is generating an answer from retrieved evidence rather than relying on the language model's memory. A grounded answer should be supported by the retrieved source material. When evidence is insufficient, the system should acknowledge the gap instead of guessing.
Learning objectives
- Generate answers using injected retrieval context.
- Check whether answer claims are supported by source chunks.
- Return a fallback when supporting context is missing.
- Compare grounded and ungrounded answers.
1. Generate from context only
Use the augmented prompt built in the previous step and make the grounding requirement explicit.
def generate_grounded_answer(question, retrieved_chunks):
    prompt_data = build_prompt(question, retrieved_chunks)
    answer = call_llm(prompt_data["prompt"])
    return {
        "question": question,
        "answer": answer,
        "context": prompt_data["prompt"],
        "sources": prompt_data["sources_used"]
    }
Key idea: Each factual claim in the answer should be traceable to one or more retrieved chunks. The prompt should instruct the model to use only supplied context, cite its sources, and explicitly acknowledge missing information.
build_prompt, call_llm, and retrieve are functions from earlier stages of the RAG pipeline; connect them to your implementation before running these snippets.

2. Handle missing support
Test a question for which retrieval returns no relevant chunks, or for which the retrieved text does not answer the question.
def answer_query(question):
    chunks = retrieve(question, k=4)

    if not chunks:
        return {
            "answer": "I don't have enough information in the provided context.",
            "sources": []
        }

    return generate_grounded_answer(question, chunks)
Important: Nonempty retrieval results do not guarantee relevant evidence. For a production system, also check retrieval relevance and whether the context actually supports the answer. Similarity-score thresholds must be calibrated to your database's scoring convention and your evaluation set.
3. Compare with and without retrieval
Ask the same question directly and through the RAG pipeline.
question = "What evidence is required for project submission?"

ungrounded = call_llm(f"Answer this question: {question}")
grounded = answer_query(question)

print("without retrieval:", ungrounded)
print("with retrieval:", grounded["answer"])
print("sources:", grounded["sources"])
The direct answer may be fluent but is not necessarily tied to your corpus. The grounded answer should reflect retrieved material and provide source metadata or citations.
4. Verify grounding
Inspect the answer and its cited sources.
def print_grounding_check(result):
    print("answer:", result["answer"])
    print("sources:")
    for source in result["sources"]:
        print(source)

print_grounding_check(grounded)
For a stronger check, identify each factual claim, locate the supporting passage, verify that citations refer to the right chunk, and flag unsupported statements. Include questions with missing or conflicting evidence in your test set.
Practical checklist
- [ ] The question is retrieved against the indexed corpus.
- [ ] The answer prompt includes relevant source chunks.
- [ ] The model is instructed not to invent missing facts.
- [ ] Answers expose source references.
- [ ] Missing-support questions produce a clear fallback.
- [ ] Grounded and ungrounded outputs are compared.
- [ ] Factual claims and citations are spot-checked against source text.
Key takeaway
Grounding reduces hallucinations by providing evidence and constraining the model's answer. It does not guarantee correctness: retrieval quality, citation accuracy, relevance checks, and evaluation remain essential.
