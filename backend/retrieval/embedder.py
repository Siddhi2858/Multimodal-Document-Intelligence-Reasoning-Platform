"""
retrieval/embedder.py
---------------------
Step 4 of Phase 3: turn text into vectors (embeddings).

We use a pretrained Sentence Transformer. Nothing is trained here.
Texts with similar meaning end up close together in vector space,
which is what lets us search a PDF by meaning instead of by keywords.

Model: all-MiniLM-L6-v2  ->  384-dimensional vectors, small and fast.
"""

from sentence_transformers import SentenceTransformer

MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_DIM = 384

_model: SentenceTransformer | None = None


def get_model() -> SentenceTransformer:
    """Load the model once and reuse it (loading is slow)."""
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def embed(texts: list[str], batch_size: int = 32) -> list[list[float]]:
    """
    Embed a list of texts. Returns one vector (list of 384 floats) per text.

    Vectors are normalised to length 1, so cosine similarity
    is just a dot product.
    """
    if not texts:
        return []

    vectors = get_model().encode(
        texts,
        batch_size=batch_size,
        normalize_embeddings=True,
        show_progress_bar=False,
    )
    return vectors.tolist()


def embed_query(question: str) -> list[float]:
    """Embed a single question."""
    return embed([question])[0]


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Cosine similarity of two normalised vectors."""
    return sum(x * y for x, y in zip(a, b))


if __name__ == "__main__":
    # Manual test:  python -m retrieval.embedder
    sentences = [
        "The Random Forest model predicts school infrastructure quality.",   # A
        "A machine learning classifier estimates how good school buildings are.",  # B (similar to A)
        "The recipe needs two cups of flour and a pinch of salt.",           # C (unrelated)
    ]

    print(f"Loading model '{MODEL_NAME}' (first run downloads ~90 MB)...")
    vecs = embed(sentences)

    print(f"Vector length: {len(vecs[0])} (expected {EMBEDDING_DIM})")
    print(f"A vs B (similar)  : {cosine_similarity(vecs[0], vecs[1]):.3f}")
    print(f"A vs C (unrelated): {cosine_similarity(vecs[0], vecs[2]):.3f}")

    ok = cosine_similarity(vecs[0], vecs[1]) > cosine_similarity(vecs[0], vecs[2])
    print("\nTEST PASSED" if ok else "\nTEST FAILED: similar pair should score higher")