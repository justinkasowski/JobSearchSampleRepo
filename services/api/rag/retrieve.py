import re
from typing import Any, Dict, List, Optional, Tuple

import requests

from config import AVAILABLE_CORPORA, MODEL, OLLAMA_URL, RAG_PROMPT, OLLAMA_KEEP_ALIVE, LOCAL_RUN
from .rag_store import get_vector_store


def corpus_has_documents(corpus: str) -> bool:
    corpus = corpus.strip().lower()

    if corpus == "all":
        return any(corpus_has_documents(name) for name in AVAILABLE_CORPORA)

    vs = get_vector_store(corpus)
    try:
        docs = vs.similarity_search("test", k=1)
        return len(docs) > 0
    except Exception:
        return False


def _normalize_filter(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    value = value.strip().lower()
    if not value or value == "all":
        return None
    return value


def _build_filter(section: Optional[str], document_type: Optional[str]) -> Optional[dict]:
    clauses = []

    wanted_section = _normalize_filter(section)
    wanted_doc_type = _normalize_filter(document_type)

    if wanted_section is not None:
        clauses.append({"section": {"$eq": wanted_section}})

    if wanted_doc_type is not None:
        clauses.append({"document_type": {"$eq": wanted_doc_type}})

    if not clauses:
        return None

    if len(clauses) == 1:
        return clauses[0]

    return {"$and": clauses}


def _format_context(docs: List[Any]) -> str:
    if not docs:
        return "No relevant context found."

    blocks = []
    for i, doc in enumerate(docs, start=1):
        meta = doc.metadata or {}
        block = (
            f"[Source {i}]\n"
            f"doc_id: {meta.get('doc_id', 'unknown')}\n"
            f"corpus: {meta.get('corpus', 'unknown')}\n"
            f"section: {meta.get('section', 'unknown')}\n"
            f"document_type: {meta.get('document_type', 'unknown')}\n"
            f"page: {meta.get('page', 'unknown')}\n"
            f"content:\n{doc.page_content}"
        )
        blocks.append(block)

    return "\n\n".join(blocks)


def _citations(docs: List[Any]) -> List[Dict[str, Any]]:
    citations = []
    for i, doc in enumerate(docs, start=1):
        meta = doc.metadata or {}
        snippet = (doc.page_content or "").strip()
        citations.append({
            "source": i,
            "doc_id": meta.get("doc_id"),
            "corpus": meta.get("corpus"),
            "section": meta.get("section"),
            "document_type": meta.get("document_type"),
            "page": meta.get("page"),
            "source_path": meta.get("source_path"),
            "snippet": snippet[:700],
        })
    return citations


def _search_single_corpus(corpus: str, question: str, candidate_k: int, search_filter: Optional[dict]) -> List[Tuple[Any, float]]:
    vs = get_vector_store(corpus)

    try:
        results = vs.similarity_search_with_score(question, k=candidate_k, filter=search_filter)
        return results
    except Exception:
        docs = vs.similarity_search(question, k=candidate_k, filter=search_filter)
        return [(doc, 0.0) for doc in docs]


def _retrieve_docs(
    corpus: str,
    question: str,
    k: int,
    section: Optional[str],
    document_type: Optional[str],
) -> List[Any]:
    candidate_k = max(k * 3, 10)
    search_filter = _build_filter(section, document_type)

    if corpus == "all":
        pooled = []
        for corpus_name in AVAILABLE_CORPORA:
            pooled.extend(_search_single_corpus(corpus_name, question, candidate_k, search_filter))

        pooled.sort(key=lambda x: x[1])
        return [doc for doc, _score in pooled[:k]]

    results = _search_single_corpus(corpus, question, candidate_k, search_filter)
    results.sort(key=lambda x: x[1])
    return [doc for doc, _score in results[:k]]


def rag_answer(
    corpus: str,
    question: str,
    k: int = 4,
    section: Optional[str] = None,
    document_type: Optional[str] = None,
    keep_alive: Optional[str] = None,
    include_prompt: bool = True,
) -> Dict[str, Any]:
    corpus = corpus.strip().lower()
    docs = _retrieve_docs(corpus, question, k, section, document_type)

    context = _format_context(docs)

    prompt = f"""{RAG_PROMPT}
CONTEXT:
{context}

QUESTION:
{question}
"""

    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
    }

    if LOCAL_RUN:
        payload["keep_alive"] = keep_alive or OLLAMA_KEEP_ALIVE

    r = requests.post(
        OLLAMA_URL,
        json=payload,
        timeout=300,
        stream=False
    )
    r.raise_for_status()
    data = r.json()

    answer = data.get("response", "").strip()
    answer = re.sub(r"\[Source\s*(\d+)\]", r"[\1]", answer)

    used_sources = sorted(set(int(x) for x in re.findall(r"\[(\d+)\]", answer)))

    refs = []
    for i in used_sources:
        if 1 <= i <= len(docs):
            meta = docs[i - 1].metadata or {}
            refs.append(f"{i}: {meta.get('doc_id', 'unknown')}, page {meta.get('page', 'unknown')}")

    if refs:
        answer += "\n\n" + "\n".join(refs)

    return {
        "corpus": corpus,
        "question": question,
        "section": section,
        "document_type": document_type,
        "answer": answer,
        "citations": _citations(docs),
        "prompt": prompt if include_prompt else None,
    }