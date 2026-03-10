from pathlib import Path
from typing import Dict, List
import uuid

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import VECTOR_BACKEND
from .rag_store import get_vector_store

PDF_BASE_DIR = Path("/data/pdfs")


def _infer_document_type(filename: str) -> str:
    name = filename.lower()
    if "_guide" in name:
        return "guide"
    if "_faq" in name:
        return "faq"
    if "_casestudy" in name:
        return "casestudy"
    return "general"


def _load_pdfs(corpus_dir: Path, corpus: str) -> List:
    docs = []

    for pdf_path in sorted(corpus_dir.rglob("*.pdf")):
        relative_path = pdf_path.relative_to(corpus_dir)
        section = relative_path.parts[0].lower() if len(relative_path.parts) > 1 else "general"

        loader = PyPDFLoader(str(pdf_path))
        pdf_docs = loader.load()

        for page_idx, d in enumerate(pdf_docs):
            d.metadata["doc_id"] = pdf_path.name
            d.metadata["corpus"] = corpus
            d.metadata["section"] = section
            d.metadata["document_type"] = _infer_document_type(pdf_path.name)
            d.metadata["source_path"] = str(pdf_path)
            d.metadata["page"] = d.metadata.get("page", page_idx)
            d.metadata["chunk_namespace"] = f"{corpus}:{pdf_path.name}"

        docs.extend(pdf_docs)

    return docs


def ingest_corpus(corpus: str, clean_rebuild: bool = False) -> Dict:
    corpus = corpus.strip().lower()
    corpus_dir = PDF_BASE_DIR / corpus

    if not corpus_dir.exists():
        raise FileNotFoundError(f"Corpus folder not found: {corpus_dir}")

    raw_docs = _load_pdfs(corpus_dir, corpus)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=900,
        chunk_overlap=150,
        separators=["\n\n", "\n", " ", ""],
    )

    chunks = splitter.split_documents(raw_docs)

    ids = []
    for i, chunk in enumerate(chunks):
        meta = chunk.metadata or {}
        stable_id = f"{meta.get('corpus','unknown')}:{meta.get('doc_id','unknown')}:{meta.get('page','0')}:{i}"
        ids.append(stable_id)

    vs = get_vector_store(corpus)

    if clean_rebuild:
        if VECTOR_BACKEND == "pgvector":
            vs.delete_collection()
            vs = get_vector_store(corpus)
        else:
            vs.delete_collection()
            vs = get_vector_store(corpus)

    vs.add_documents(chunks, ids=ids)

    if VECTOR_BACKEND != "pgvector":
        vs.persist()

    return {
        "corpus": corpus,
        "clean_rebuild": clean_rebuild,
        "vector_backend": VECTOR_BACKEND,
        "pdf_dir": str(corpus_dir),
        "pdf_files": len(list(corpus_dir.rglob('*.pdf'))),
        "pages_loaded": len(raw_docs),
        "chunks_added": len(chunks),
    }