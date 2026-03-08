import os
from pathlib import Path
from typing import Optional

from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

# Persist Chroma DB inside the container
CHROMA_BASE_DIR = Path(os.getenv("CHROMA_BASE_DIR", "/data/chroma"))
EMBED_MODEL_NAME = os.getenv("EMBED_MODEL_NAME", "sentence-transformers/all-MiniLM-L6-v2")

_embeddings_singleton: Optional[HuggingFaceEmbeddings] = None


def get_embeddings() -> HuggingFaceEmbeddings:
    global _embeddings_singleton
    if _embeddings_singleton is None:
        _embeddings_singleton = HuggingFaceEmbeddings(model_name=EMBED_MODEL_NAME)
    return _embeddings_singleton


def get_vector_store(corpus: str) -> Chroma:
    """
    One Chroma collection per corpus. Persisted to disk so ingest doesn't need to run every time.
    """
    corpus = corpus.strip().lower()
    persist_dir = CHROMA_BASE_DIR / corpus
    persist_dir.mkdir(parents=True, exist_ok=True)

    return Chroma(
        collection_name=f"{corpus}_docs",
        embedding_function=get_embeddings(),
        persist_directory=str(persist_dir),
    )