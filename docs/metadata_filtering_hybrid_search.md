Similarity search finds text with related meaning, but sometimes the best result must come from a specific source, section, date, user group, or document type. Metadata filtering scopes retrieval before or during vector search. Hybrid search can add keyword matching when exact terms, IDs, or names matter.
Learning objectives
By the end, you'll be able to:
- Restrict vector retrieval using metadata filters.
- Compare filtered and unfiltered results for a query.
- Explain vector search versus keyword search.
- Use optional hybrid matching to improve precision.
Filter retrieval to the right subset
An unfiltered query searches the whole corpus. A filtered query searches only records whose metadata matches the filter.
def retrieve(query, k=3, metadata_filter=None):
    query_vector = embed([query], model=EMBEDDING_MODEL)[0]
    return collection.search(
        vector=query_vector,
        top_k=k,
        filter=metadata_filter,
        include=["text", "metadata", "score"]
    )

query = "What are the password reset steps?"

unfiltered = retrieve(query, k=3)
filtered = retrieve(
    query,
    k=3,
    metadata_filter={"section": "Account access"}
)
The filtered result should be more precise when metadata reflects the user's intent. For example, a password query filtered to section = Account access should avoid unrelated security policy or campus IT chunks.
Implementation note: collection.search, its filter syntax, and returned score format are illustrative. Adapt them to the specific vector database client.

Show the effect
Print both result sets so you can compare sources, scores, and text.
def show_results(label, results):
    print(label)
    for item in results:
        print("score:", round(item["score"], 4))
        print("source:", item["metadata"]["source"])
        print("section:", item["metadata"].get("section"))
        print("text:", item["text"][:120])

show_results("unfiltered", unfiltered)
show_results("filtered", filtered)
Filtering can improve precision when it removes plausible but wrong areas of the corpus. It can hurt recall if the filter is too strict or metadata is missing.
Add optional keyword or hybrid matching
Vector search is semantic: it can match meaning even when wording differs. Keyword search is lexical: it rewards exact words, names, IDs, and phrases. Hybrid search combines both.
def keyword_score(text, keywords):
    lowered = text.lower()
    return sum(1 for word in keywords if word.lower() in lowered)

def hybrid_rank(vector_results, keywords, vector_weight=0.8, keyword_weight=0.2):
    ranked = []
    for item in vector_results:
        lexical = keyword_score(item["text"], keywords)
        combined = (vector_weight * item["score"]) + (keyword_weight * lexical)
        ranked.append({**item, "keyword_score": lexical, "hybrid_score": combined})
    return sorted(ranked, key=lambda item: item["hybrid_score"], reverse=True)

hybrid = hybrid_rank(filtered, keywords=["password", "reset"])
show_results("hybrid filtered", hybrid)
This example reranks vector candidates, rather than performing a full hybrid search across the entire corpus. For production hybrid retrieval, combine candidates from independent lexical and vector searches, and normalize scores or use reciprocal rank fusion before combining them; raw vector similarity and keyword counts are not necessarily comparable.

Hybrid search is useful when users search for exact product names, policy IDs, error codes, course codes, or people, where pure semantic similarity might miss exact-match requirements.
Choose filters from the product need
Useful metadata filters may include user role, document type, department, product, date, region, language, section, or access level. Store the needed metadata during ingestion. Enforce access permissions at the retrieval layer, not just through user-controlled filters.
Key takeaways
- Vector search: matches meaning.
- Keyword search: matches terms and identifiers.
- Metadata filtering: restricts the searchable records.
- Hybrid search: combines semantic and lexical evidence.
- Evaluation: compare relevance and recall on representative user queries before deciding which strategy works best.
