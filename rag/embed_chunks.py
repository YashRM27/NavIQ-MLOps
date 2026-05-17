"""
embed_chunks.py
---------------
Reads chunks.jsonl, embeds each chunk using HuggingFace sentence-transformers,
and stores everything in a local ChromaDB vector database.

Run: python rag/embed_chunks.py

First run will download the embedding model (~90MB). Subsequent runs are instant.
"""

import json
import os
from sentence_transformers import SentenceTransformer
import chromadb

CHUNKS_FILE = os.path.join("data", "chunks.jsonl")
CHROMA_DIR  = os.path.join("data", "chroma_db")

# Best free model for semantic search — small, fast, good quality
EMBED_MODEL = "all-MiniLM-L6-v2"

# ChromaDB collection name
COLLECTION  = "mutual_funds"


def load_chunks(path: str) -> list[dict]:
    chunks = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                chunks.append(json.loads(line))
    return chunks


def main():
    # Load chunks
    print("Loading chunks...")
    chunks = load_chunks(CHUNKS_FILE)
    print(f"Chunks loaded: {len(chunks)}")

    # Load embedding model
    print(f"\nLoading embedding model: {EMBED_MODEL}")
    print("(First run downloads ~90MB — wait for it...)")
    model = SentenceTransformer(EMBED_MODEL)
    print("Model ready.")

    # Extract texts and metadata
    texts    = [c["chunk_text"]  for c in chunks]
    ids      = [str(c["scheme_code"]) for c in chunks]
    names    = [c["fund_name"]   for c in chunks]

    # Build flat metadata dicts (ChromaDB only accepts str/int/float/bool)
    metadatas = []
    for c in chunks:
        m = {k: (v if v is not None else -999)
             for k, v in c["metadata"].items()}
        m["fund_name"] = c["fund_name"]
        metadatas.append(m)

    # Generate embeddings
    print(f"\nEmbedding {len(texts)} chunks...")
    embeddings = model.encode(texts, show_progress_bar=True).tolist()
    print("Embeddings done.")

    # Set up ChromaDB (HTTP client — connects to ChromaDB container)
    print(f"\nConnecting to ChromaDB at {os.getenv('CHROMA_HOST', 'localhost')}:{os.getenv('CHROMA_PORT', 8000)}")
    client = chromadb.HttpClient(
        host=os.getenv("CHROMA_HOST", "localhost"),
        port=int(os.getenv("CHROMA_PORT", 8000))
    )

    # Delete existing collection if re-running
    existing = [c.name for c in client.list_collections()]
    if COLLECTION in existing:
        client.delete_collection(COLLECTION)
        print("Deleted old collection.")

    collection = client.create_collection(
        name=COLLECTION,
        metadata={"hnsw:space": "cosine"}   # cosine similarity for text
    )

    # Add to ChromaDB
    collection.add(
        documents  = texts,
        embeddings = embeddings,
        metadatas  = metadatas,
        ids        = ids
    )

    print(f"\nStored {collection.count()} funds in ChromaDB.")
    print(f"Location: {CHROMA_DIR}")

    # Quick sanity test
    print("\nRunning sanity check query: 'best large cap fund with high returns'")
    results = collection.query(
        query_embeddings = model.encode(["best large cap fund with high returns"]).tolist(),
        n_results        = 3
    )
    print("Top 3 results:")
    for i, meta in enumerate(results["metadatas"][0]):
        print(f"  {i+1}. {meta['fund_name']} | 3Y CAGR: {meta['cagr_3y']}%")


if __name__ == "__main__":
    main()
