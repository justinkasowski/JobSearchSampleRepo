import os
from pathlib import Path
from typing import Optional

from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_postgres import PGVector

from config import VECTOR_BACKEND, PGVECTOR_CONNECTION_STRING, EMBED_MODEL_NAME

CHROMA_BASE_DIR = Path(os.getenv("CHROMA_BASE_DIR", "/data/chroma"))

_embeddings_singleton: Optional[HuggingFaceEmbeddings] = None


def get_embeddings() -> HuggingFaceEmbeddings:
    global _embeddings_singleton
    if _embeddings_singleton is None:
        _embeddings_singleton = HuggingFaceEmbeddings(model_name=EMBED_MODEL_NAME)
    return _embeddings_singleton


def get_vector_store(corpus: str):
    corpus = corpus.strip().lower()

    if VECTOR_BACKEND == "pgvector":
        return PGVector(
            embeddings=get_embeddings(),
            collection_name=f"{corpus}_docs",
            connection=PGVECTOR_CONNECTION_STRING,
            use_jsonb=True,
        )

    persist_dir = CHROMA_BASE_DIR / corpus
    persist_dir.mkdir(parents=True, exist_ok=True)

    return Chroma(
        collection_name=f"{corpus}_docs",
        embedding_function=get_embeddings(),
        persist_directory=str(persist_dir),
    )