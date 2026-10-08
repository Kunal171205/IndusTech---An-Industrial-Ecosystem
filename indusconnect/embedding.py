"""
indusconnect/embedding.py
==========================
Shared embedding module for IndusConnect.

The SAME SentenceTransformer model is used for:
  - Worker profile text
  - Job listing text
  - Search queries

Model: sentence-transformers/all-MiniLM-L6-v2
Dimensions: 384
Normalization: L2 (so inner product == cosine similarity in FAISS IndexFlatIP)
"""

import os
import logging
import numpy as np
from typing import List, Optional, Union

logger = logging.getLogger("[EMBEDDING]")

_EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
_EMBEDDING_DIM = 384

# ── Lazy model singleton ──────────────────────────────────────────────────────
_model = None


class DummyModel:
    def encode(self, texts, **kwargs):
        # Return a zero matrix of size (len(texts), 384)
        return np.zeros((len(texts), _EMBEDDING_DIM), dtype=np.float32)

def get_model():
    """Return the shared SentenceTransformer model, loading it once."""
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            logger.info(f"Loading embedding model: {_EMBEDDING_MODEL_NAME}")
            _model = SentenceTransformer(_EMBEDDING_MODEL_NAME)
            logger.info(f"Embedding model ready. Dimension={_EMBEDDING_DIM}")
        except OSError as e:
            logger.error(f"OS Memory Error while loading model (likely page file too small): {e}")
            logger.warning("Using dummy embeddings to allow the pipeline to proceed.")
            _model = DummyModel()
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise
    return _model


def embed_texts(texts: List[str], batch_size: int = 64) -> np.ndarray:
    """
    Embed a list of texts into L2-normalized vectors.
    """
    if not texts:
        return np.array([])
    
    try:
        model = get_model()
        vecs = model.encode(texts, batch_size=batch_size, show_progress_bar=False)
        vecs = np.array(vecs, dtype=np.float32)
        norms = np.linalg.norm(vecs, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1.0, norms)  # avoid divide-by-zero
        vecs = vecs / norms
        return vecs
    except Exception as e:
        logger.error(f"Failed to generate embeddings (likely Out Of Memory): {e}")
        logger.warning("Using dummy embeddings to allow the pipeline to proceed.")
        return np.zeros((len(texts), _EMBEDDING_DIM), dtype=np.float32)


def embed_single(text: str) -> Optional[np.ndarray]:
    """
    Embed a single text string.

    Returns:
        L2-normalized float32 vector of shape (1, 384), or None on error.
    """
    if not text or not text.strip():
        return None
    try:
        return embed_texts([text])
    except Exception as e:
        logger.error(f"Embedding failed: {e}")
        return None


def cosine_similarity(vec_a: np.ndarray, vec_b: np.ndarray) -> float:
    """
    Cosine similarity between two L2-normalized vectors.
    Since both are normalized, this is just the dot product.
    """
    return float(np.dot(vec_a.flatten(), vec_b.flatten()))
