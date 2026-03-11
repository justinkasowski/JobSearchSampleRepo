# RAG LLM System

[ Click here to run the deployed model ](https://rag-demo.justinkasowski.com) Note* The deployed version points at a private repo and will be a continuation past v0.99

This repository contains a Retrieval-Augmented Generation (RAG) LLM service designed to ingest corpora of documents and answer questions with cited sources. The system can optionally trigger integrations such as Slack or Discord notifications when follow-up actions are detected.

This README provides a **generic guide to using the deployed LLM system**. For implementation details and deeper documentation, see the following documents:

- **Architecture** – [`/docs/architecture.md`](docs/architecture.md)
  Directory layout and explanation of core system components.

- **Deployment** – [`/docs/deployment.md`](docs/deployment.md)
  Guide for deploying the system to cloud infrastructure.

- **Developers** – [`/docs/developers.md`](docs/developers.md)
  Instructions for installing dependencies and running the system locally.

- **Use Cases** – [`/docs/use_cases.md`](docs/use_cases.md)  
  Examples of real-world applications for this type of system.

- **Version History and Development Plan** – [`/docs/version_history.md`](docs/version_history.md)  
  Roadmap and summary of past development milestones.

---

# System Overview

The system provides a web interface for interacting with a hosted LLM that performs retrieval-augmented question answering.

High-level flow:

```
User
 ↓
Web UI
 ↓
FastAPI backend
 ↓
RAG retrieval
 ↓
LLM inference (Ollama)
 ↓
Answer with citations
```

Documents are ingested into a corpus and indexed for retrieval. Queries then search those indexed documents and feed relevant context to the model.

---

# Using the Deployed System

## 1. Access the Web Interface

Open the hosted application in a browser:

```
https://rag-demo.justinkasowski.com
```

The interface contains three primary sections:

- Corpus Ingestion
- RAG Query
- Integration Controls

---

# Ingesting Documents

Before querying the system, documents must be ingested into the corpus.

Steps:

1. Navigate to the **Ingest Corpus** panel.
2. Provide the location of the document files.
3. Specify metadata fields such as:
   - corpus
   - section
   - document type
4. Run the ingestion process.

During ingestion the system performs:

```
read documents
 ↓
split text into chunks
 ↓
generate embeddings
 ↓
store vectors and metadata
```

Once completed, the corpus becomes searchable.

---

# Querying the Corpus

To ask questions about the ingested documents:

1. Navigate to the **RAG Query** panel.
2. Enter a question in natural language.
3. Select optional filters:

   - corpus
   - section
   - document type
   - top-k retrieval count

4. Click **Run Query**.

The system will:

```
retrieve relevant document chunks
 ↓
construct prompt with context
 ↓
run inference with the LLM
 ↓
return answer with citations
```

Responses include the supporting documents used to generate the answer.

---

# Direct Model Query (Optional)

If corpus retrieval is disabled, the system can query the language model directly.

This mode bypasses document retrieval and sends the prompt straight to the model.

Use this when:

- testing model behavior
- generating text unrelated to the corpus
- validating prompt structure

---

# Integration Detection

The system can detect follow-up actions embedded in model responses.

Supported integrations include:

- Slack
- Discord

When enabled, the system evaluates responses for actionable instructions and may generate a message plan for external systems.

Example workflow:

```
model response
 ↓
integration detection
 ↓
message plan generation
 ↓
user approval
 ↓
message sent to integration
```

---

# Health Monitoring

The system exposes a health endpoint used by monitoring systems:

```
GET /health
```

This endpoint verifies that:

- the backend service is running
- the configured model is reachable
- the inference endpoint responds correctly

A scheduled health check can optionally publish heartbeat messages to monitoring channels.

---

# Typical Workflow

```
1. Deploy system
2. Ingest document corpus
3. Run RAG queries
4. Review citations
5. Trigger integrations when appropriate
```

This enables structured document knowledge to be queried conversationally while maintaining traceable sources.

---

# Summary

This system provides:

- Retrieval-augmented question answering
- Document citation for model responses
- Web interface for ingestion and querying
- Integration hooks for operational workflows
- Cloud-deployable inference architecture

For details about implementation and development, refer to the documents in `/docs/`.
