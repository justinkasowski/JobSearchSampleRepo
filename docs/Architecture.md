```text
User
  |
  v
FastAPI API
  |
  v
RAG Pipeline
  |      |
  v      v
Chroma   Ollama
  |
  v
PDF Documents
```

```                         
|-- README.md                 Project overview and run instructions
|-- docker-compose.yml        Defines Ollama and FastAPI containers
|-- run.bat                   Windows startup script
|-- run.sh                    Linux/macOS startup script
|-- cleanup.bat               Windows cleanup script
|-- cleanup.sh                Linux/macOS cleanup script
|
|-- docs/                     === Project documentation === 
|   |-- Architecture.md         System architecture and repo structure (You're looking at it!)
|
|-- data/                     |===  Persistent runtime data ===|
|   |-- pdfs/                 |== Source documents used for RAG indexing ==|
|   |   |-- policy/             Example policy document corpus
|   |   |-- hr/                 Example HR document corpus
|   |   |-- sales/              Example sales document corpus
|   |-- chroma/               |== Persisted vector database storage ==|
|
|-- services/                 |===  Application services === |
    |-- api/                  |== FastAPI backend service ==|
        |-- Dockerfile          
        |-- requirements.txt    Python dependencies
        |-- main.py             FastAPI API endpoints
        |-- rag/              |= RAG pipeline components =|
        |   |-- rag_store.py    Initializes Chroma vector store
        |   |-- ingest.py       PDF ingestion and embedding
        |   |-- retrieve.py     Retrieval and prompt construction
        |-- llm/              |= Ollama client utilities =|
```