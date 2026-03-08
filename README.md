# JobSearchSampleRepo (Local LLM + LangChain RAG)

This repo runs:
- Ollama (local LLM server) in Docker
- FastAPI backend that calls Ollama and provides RAG endpoints
- LangChain + Chroma for PDF RAG (per-corpus)

## Prereqs
- Docker Desktop (Windows/macOS) or Docker Engine (Linux)

## Quickstart

### 1) Start everything
Windows:
- double click `run.bat`

Linux/macOS:
```bash
./run.sh