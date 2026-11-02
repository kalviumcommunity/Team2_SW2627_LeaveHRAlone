Overview
Once a vector database collection has been created, the next step is to load the corpus records into it. Indexing means inserting chunk embeddings into the vector database so they can be searched, while retaining the source text and metadata for retrieval, citations, and filtering.
Learning objectives
By the end of this lesson, you will be able to:
- Insert all corpus embeddings into a vector database.
- Store each vector alongside its source text and metadata.
- Confirm the indexed count matches the chunk count.
- Spot-check stored records against the original chunks.
1. Prepare records for indexing
Each indexed record should contain:
Field	Purpose
id	Stable identifier for re-indexing and updates
vector	Numerical embedding used for similarity search
text	Original chunk text used in retrieved answers
metadata	Source information for citations and filtering


def to_vector_record(chunk):
    return {
        "id": chunk["id"],
        "vector": chunk["embedding"],
        "text": chunk["text"],
        "metadata": {
            "source": chunk["metadata"]["source"],
            "chunk_index": chunk["metadata"]["chunk_index"],
            "section": chunk["metadata"].get("section")
        }
    }

records = [to_vector_record(chunk) for chunk in embedded_chunks]
Metadata makes it possible to filter retrieval by document type, source, date range, or section, provided those fields were stored during indexing.
Note: This example uses a conceptual collection.upsert() and collection.get() interface. Actual method names and record formats vary by vector database. Some databases require text and metadata inside a payload object; some reject None metadata values.

2. Bulk insert and verify counts
Use batches to avoid overloading the database client with a large corpus.
def batches(items, size):
    for start in range(0, len(items), size):
        yield items[start:start + size]

inserted = 0
failures = []

for batch in batches(records, size=100):
    try:
        collection.upsert(batch)
        inserted += len(batch)
    except Exception as error:
        failures.append({
            "batch_start_id": batch[0]["id"],
            "error": str(error)
        })

indexed_count = collection.count()
expected_count = len(embedded_chunks)

print("expected chunks:", expected_count)
print("inserted this run:", inserted)
print("indexed count:", indexed_count)
print("failures:", failures)

assert not failures, "some batches failed to index"
assert indexed_count == expected_count, "indexed count does not match chunk count"
Important: A matching total count is meaningful only if the collection contains exactly this corpus (or the count is filtered to this corpus). Existing unrelated records can distort the comparison. Also, a successful API response does not always mean data is immediately queryable; check whether your database performs asynchronous indexing.
3. Spot-check integrity
Read back a known chunk and verify that its text, source, and embedding dimensions match the original.
sample = embedded_chunks[0]
stored = collection.get(sample["id"])

assert stored["text"] == sample["text"]
assert stored["metadata"]["source"] == sample["metadata"]["source"]
assert len(stored["vector"]) == len(sample["embedding"])

print("spot check passed:", sample["id"])
print("source:", stored["metadata"]["source"])
print("text preview:", stored["text"][:120])
For stronger validation, sample multiple IDs across documents and verify the stored vector values (or a checksum), not only their dimensions.
4. When documents change
Use stable chunk IDs and a document version or content hash to update the index efficiently:
1. Identify unchanged chunks and leave them alone.
2. Upsert new or modified chunks.
3. Delete records for chunks that no longer exist.
4. Recheck counts and spot-check representative records.
This is incremental indexing, which avoids rebuilding the entire collection for small changes.
5. Watch and learn
Vector Databases Explained — IBM Technology

Focus on how vector databases store embeddings for similarity search and how indexing connects embeddings with text and metadata. Search the video title and channel if the video does not load.
Key takeaway
Indexing is complete only when the expected records are stored and verified. Check batch failures, record counts, and the integrity of retrieved text, metadata, and vectors before building the retrieval pipeline.
