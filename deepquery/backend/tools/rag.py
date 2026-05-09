import numpy as np
from openai import AsyncOpenAI

_embed_client = AsyncOpenAI()


async def embed_texts(texts: list[str]) -> np.ndarray:
    """Embed a list of texts with text-embedding-3-small. Returns (N, D) array."""
    response = await _embed_client.embeddings.create(
        model="text-embedding-3-small",
        input=texts,
    )
    vectors = [d.embedding for d in response.data]
    return np.array(vectors, dtype=np.float32)


def cosine_similarity(query_vec: np.ndarray, corpus_vecs: np.ndarray) -> np.ndarray:
    """Compute cosine similarity between one query vector and N corpus vectors."""
    q = query_vec / (np.linalg.norm(query_vec) + 1e-10)
    norms = np.linalg.norm(corpus_vecs, axis=1, keepdims=True) + 1e-10
    c = corpus_vecs / norms
    return c @ q


async def retrieve_top_k(query: str, chunks: list[dict], k: int = 8) -> list[dict]:
    """
    Given a query string and a list of chunk dicts (with 'abstract' field),
    return the top-k most relevant chunks by cosine similarity.
    """
    if not chunks:
        return []

    texts = [c["abstract"] for c in chunks]
    all_texts = [query] + texts
    vecs = await embed_texts(all_texts)

    query_vec = vecs[0]
    corpus_vecs = vecs[1:]

    scores = cosine_similarity(query_vec, corpus_vecs)
    top_indices = np.argsort(scores)[::-1][:k]

    return [chunks[i] for i in top_indices]
