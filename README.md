# JobSearchSampleRepo (Local LLM + LangChain RAG)

This repo runs:
- Ollama (local LLM server) in Docker
- FastAPI backend that calls Ollama and provides RAG endpoints
- LangChain + Chroma for PDF RAG (per-corpus)

Note* Local model has placeholders for websockets, to use the integrations with Slack/Discord, see the deployed version at https://jobsearchsamplerepo-37975938497.us-east4.run.app/

Slack - https://join.slack.com/t/jobsearchsamplerepo/shared_invite/zt-3rv3m9rmr-0fZsxWpXCgGtEG4WM2aQYw

Discord - https://discord.gg/2drHu6kT

## Prereqs
- Docker Desktop (Windows/macOS) or Docker Engine (Linux)
- Nvidia Drivers 

## Quickstart

### 1) Start everything
Windows:
- double click `run.bat`

Linux/macOS:
```bash
sudo chmod +x ./run.sh
./run.sh
```

If it doesn't open automatically, connect to the UI at http://localhost:8000/

#TODO Update this significantly 