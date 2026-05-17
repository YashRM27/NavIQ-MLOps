"""
retriever.py
------------
Given a user query, retrieves the top-k most relevant fund chunks
from ChromaDB using semantic similarity.

Can be imported by app.py or tested standalone.

Standalone test:
    python rag/retriever.py
"""

import os
from sentence_transformers import SentenceTransformer
import chromadb

CHROMA_DIR  = os.path.join("data", "chroma_db")
EMBED_MODEL = "all-MiniLM-L6-v2"
COLLECTION  = "mutual_funds"

# Load once at module level (avoid reloading on every query)
_model      = None
_collection = None


def _load():
    global _model, _collection
    if _model is None:
        _model = SentenceTransformer(EMBED_MODEL)
    if _collection is None:
        client = chromadb.HttpClient(
            host=os.getenv("CHROMA_HOST", "localhost"),
            port=int(os.getenv("CHROMA_PORT", 8000))
        )
        _collection = client.get_collection(COLLECTION)


def retrieve(query: str, top_k: int = 5) -> list[dict]:
    """
    Retrieve top_k fund chunks most relevant to the query.
    Returns list of dicts with keys: fund_name, chunk_text, metadata, score
    """
    _load()

    query_embedding = _model.encode([query]).tolist()

    results = _collection.query(
        query_embeddings = query_embedding,
        n_results        = top_k
    )

    hits = []
    for i in range(len(results["ids"][0])):
        hits.append({
            "fund_name"  : results["metadatas"][0][i]["fund_name"],
            "chunk_text" : results["documents"][0][i],
            "metadata"   : results["metadatas"][0][i],
            "score"      : round(1 - results["distances"][0][i], 4),  # cosine similarity
        })

    return hits


if __name__ == "__main__":
    # Test a few queries
    test_queries = [
        "best large cap fund for long term",
        "kam risk wala fund kaun sa hai",
        "SBI large cap fund performance",
        "fund with highest sharpe ratio",
    ]

    for q in test_queries:
        print(f"\nQuery: '{q}'")
        hits = retrieve(q, top_k=3)
        for h in hits:
            print(f"  → {h['fund_name']:<50} | score: {h['score']} | 3Y: {h['metadata']['cagr_3y']}%")
