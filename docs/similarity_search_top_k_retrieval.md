Overview
After indexing the corpus, retrieval begins. Embed the user's query using the same embedding model used for the documents, search the vector database, and return the top-k most similar chunks. These ranked chunks provide grounding context for a retrieval-augmented generation (RAG) system.
Learning objectives
By the end of this lesson, you will be able to:
- Embed a user query with the same model used for documents.
- Run top-k similarity search against a vector database.
- Return ranked chunks with scores and metadata.
- Compare the retrieved context for different values of k.
Query to retrieved chunks
The retrieval pipeline follows four steps:
1. Receive a user query.
2. Convert the query into an embedding.
3. Search the vector database for the nearest vectors.
4. Return ranked source chunks with their scores and metadata.
def retrieve(query, k=3):
    query_vector = embed([query], model=EMBEDDING_MODEL)[0]

    results = collection.search(
        vector=query_vector,
        top_k=k,
        include=["text", "metadata", "score"]
    )

    return [
        {
            "score": item["score"],
            "text": item["text"],
            "metadata": item["metadata"]
        }
        for item in results
    ]
Implementation note: This is database-agnostic pseudocode. Adapt collection.search, its arguments, and its response format to the vector database you use. Some databases return a distance rather than a similarity score, so check the metric and score direction before interpreting rankings.

Important: Query and document embeddings must use the same model and compatible preprocessing. Mixing embedding spaces makes the ranking unreliable, even when the database accepts the vectors.
What top-k means
Top-k means returning the k highest-ranked matching chunks. For example, k=3 returns three chunks (or fewer if the index contains fewer than three eligible records).
query = "How can a learner reset their password?"

for k in [1, 3, 5]:
    print("k =", k)
    for result in retrieve(query, k=k):
        print(result["score"], result["metadata"], result["text"][:100])
k	Benefit	Trade-off
1	Focused, minimal context	May miss supporting information
3	Often a useful starting point	Can still omit relevant chunks
5	More opportunities to retrieve supporting evidence	More tokens and potentially irrelevant context


The best k depends on chunk size, corpus quality, question complexity, and the language model's context window.
Inspect the retrieved context
Each result should contain its source text, retrieval score, and metadata for traceability.
results = retrieve("How can a learner reset their password?", k=3)

for rank, result in enumerate(results, start=1):
    print("rank:", rank)
    print("score:", round(result["score"], 4))
    print("source:", result["metadata"]["source"])
    print("chunk_index:", result["metadata"]["chunk_index"])
    print("text:", result["text"])
This output demonstrates that a user question can be mapped to ranked source chunks that can later support a grounded answer and citations.
Larger-k trade-off
Increasing k can improve recall by including more potentially relevant chunks, but it can also increase query payload size, downstream language-model token use, latency, and irrelevant context. Retrieval latency itself depends on the database and index configuration. Evaluate k against a representative set of real questions rather than choosing it arbitrarily.
Practical validation checklist
- [ ] The query uses the same embedding model as the indexed documents.
- [ ] The query embedding dimension matches the collection configuration.
- [ ] The returned chunks are ranked according to the database's score or distance semantics.
- [ ] Each returned chunk includes its text and source metadata.
- [ ] Retrieval has been tested with k=1, k=3, and k=5.
- [ ] Additional chunks are checked for relevance, not just quantity.
Further reading
- Pinecone — Semantic search
- Qdrant — Search
- Chroma — Query collections
