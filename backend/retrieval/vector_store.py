"""
retrieval/vector_store.py
-------------------------
Step 5 of Phase 3: store chunk vectors in Qdrant and search them.

Qdrant runs in LOCAL mode here (no Docker, no server). Data is saved
in a folder on disk, so it survives restarts.

Two public functions:
    add_chunks(chunks, vectors)               -> store chunks
    search(query_vector, document_id, top_k)  -> closest chunks
"""

import atexit
import uuid
from pathlib import Path

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    VectorParams,
)

COLLECTION_NAME = "document_chunks"
EMBEDDING_DIM = 384  # must match all-MiniLM-L6-v2
STORAGE_PATH = Path(__file__).resolve().parent.parent / "storage" / "qdrant"

_client: QdrantClient | None = None


def get_client() -> QdrantClient:
    """Open the local Qdrant store once and reuse it."""
    global _client
    if _client is None:
        STORAGE_PATH.mkdir(parents=True, exist_ok=True)
        _client = QdrantClient(path=str(STORAGE_PATH))
        _ensure_collection(_client)
    return _client


def close_client() -> None:
    """Close the local store cleanly (called automatically at exit)."""
    global _client
    if _client is not None:
        _client.close()
        _client = None


atexit.register(close_client)


def _ensure_collection(client: QdrantClient) -> None:
    if not client.collection_exists(COLLECTION_NAME):
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE),
        )


def add_chunks(chunks: list[dict], vectors: list[list[float]]) -> int:
    """Store chunks and their vectors. Returns the number stored."""
    if len(chunks) != len(vectors):
        raise ValueError("chunks and vectors must have the same length")
    if not chunks:
        return 0

    points = [
        PointStruct(
            # Same chunk_id always gives the same point id, so re-uploading
            # a document overwrites instead of creating duplicates.
            id=str(uuid.uuid5(uuid.NAMESPACE_URL, chunk["chunk_id"])),
            vector=vector,
            payload=chunk,
        )
        for chunk, vector in zip(chunks, vectors)
    ]
    get_client().upsert(collection_name=COLLECTION_NAME, points=points)
    return len(points)


def search(
    query_vector: list[float],
    document_id: str | None = None,
    top_k: int = 5,
) -> list[dict]:
    """
    Return the top_k most similar chunks, best first:
        {"chunk_id", "document_id", "page_number", "text", "score"}
    If document_id is given, only that document is searched.
    """
    query_filter = None
    if document_id:
        query_filter = Filter(
            must=[FieldCondition(key="document_id", match=MatchValue(value=document_id))]
        )

    response = get_client().query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        query_filter=query_filter,
        limit=top_k,
        with_payload=True,
    )

    return [{**point.payload, "score": round(point.score, 4)} for point in response.points]


def delete_document(document_id: str) -> None:
    """Remove every chunk belonging to a document."""
    get_client().delete(
        collection_name=COLLECTION_NAME,
        points_selector=Filter(
            must=[FieldCondition(key="document_id", match=MatchValue(value=document_id))]
        ),
    )


def count_chunks(document_id: str | None = None) -> int:
    """How many chunks are stored (optionally for one document)."""
    flt = None
    if document_id:
        flt = Filter(
            must=[FieldCondition(key="document_id", match=MatchValue(value=document_id))]
        )
    return get_client().count(collection_name=COLLECTION_NAME, count_filter=flt, exact=True).count


if __name__ == "__main__":
    # Manual test with fake 384-d vectors (no model needed):
    #   python -m retrieval.vector_store
    import random

    random.seed(0)

    def fake_vec(seed_axis: int) -> list[float]:
        v = [random.uniform(-0.01, 0.01) for _ in range(EMBEDDING_DIM)]
        v[seed_axis] = 1.0
        return v

    chunks = [
        {"chunk_id": "testdoc-p1-c1", "document_id": "testdoc", "page_number": 1, "text": "about cats"},
        {"chunk_id": "testdoc-p2-c1", "document_id": "testdoc", "page_number": 2, "text": "about dogs"},
        {"chunk_id": "otherdoc-p1-c1", "document_id": "otherdoc", "page_number": 1, "text": "about cars"},
    ]
    vectors = [fake_vec(0), fake_vec(1), fake_vec(0)]

    print("Stored:", add_chunks(chunks, vectors))
    print("Total chunks:", count_chunks(), "| in testdoc:", count_chunks("testdoc"))

    hits = search(fake_vec(0), document_id="testdoc", top_k=2)
    for h in hits:
        print(f"  page {h['page_number']}  score={h['score']}  text={h['text']!r}")

    ok = hits[0]["text"] == "about cats" and all(h["document_id"] == "testdoc" for h in hits)
    delete_document("testdoc")
    delete_document("otherdoc")
    print("After cleanup:", count_chunks())
    print("\nTEST PASSED" if ok else "\nTEST FAILED")