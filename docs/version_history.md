# Version History

This document tracks major milestones and planned future development.

---

## Version 0.9 – Initial Prototype

**Goal:** Deploy a cloud-based CI/CD RAG tool.

Features:
- Docker containerization
- Cloud Run deployment
- Cloud SQL database
- FastAPI backend
- Ollama model inference
- Basic RAG retrieval
- Chroma vector storage
- Web interface
- Firebase authentication and rate limiting
- SQL storage for bug reports and future fine-tuning data
- Slack / Discord integrations
- Custom domain support
- Health monitoring

---

## Version 0.99 – Hosted Vector Database

**Goal:** Production-grade vector storage.

Planned changes:
- Migrate vector storage to PostgreSQL + pgvector
- Keep Chroma for local development runs
- Optional Cloud Storage document storage
- Improved ingestion pipeline

*Timeline:* 1-2 days 

---

## Version 1.0 - Multi-Tenant Support

**Goal:** Support multiple organizations.

Planned changes:
- Admin panel for first -----@business.com
- Subsequent joins from business request permission to join organization
- Admin sets their permissions
- Admin sets storage/compute limits
- Admin reviews and accepts policies
- Admin supplies payment information
- Usage logging for billing (compute)

*Timeline:*  7-14 days

### Version 1.1 – Tenant Data Storage

**Goal:** Tenant specific data storage

Planned changes:
- Switch from `corpus / section / document_type` to `company / corpus / section`
- Corpus management UI with Cloud Storage-backed uploads
- Provide "always available" corpora across tenants (e.g. coding languages, law, healthcare)
- Usage logging for billing (storage)


*Timeline:*  3-5 days 

---

### Version 1.2 – Advanced Retrieval and Custom Integrations

**Goal:** Improve answer accuracy.

Planned changes:
- Ability to specify embedding models and chunking strategies
- Hybrid search using embeddings plus keyword search
- Semantic re-ranking
- Custom prompt definitions
- Custom schema response constraints
- Auto generated prompt for schema constraints
- Updated integration options based on schema constraint

*Timeline:* 5-7 days 

### Version 1.3 - Custom Integration Saving 

**Goal:** Toggle through multiple integration panels for different saved integrations

Planned changes: 
- Ability to save integrations and toggle them

*Timeline:* 1-2 days

### Version 1.4 - Agentic workflow

**Goal:** Multi step integration pipeline

Planned changes:  
- Provide interface to chain integration commands
  - e.g. first integration call to determine integration pipeline
  - Automatic call to outcome integration using schema-constrained return

*Timeline:* 1-2 days

---

## Version 2.0 – Scalable Cloud Structure

**Goal:** Improve scalability and production readiness.

Planned changes:
- Improved scaling architecture
- Better separation of compute, document storage, and vector storage
- More robust monitoring and operational tooling

*Timeline:* 3-4 days

### Version 2.1 - "Always on" availability for tenants
**Goal:** Eliminate cold starts for tenants

Planned changes: 
- Tenant specific always-on inference containers 
- URL redirection to client inference containers (e.g. llmlab.cloud/mybusiness/)

*Timeline:* 1-2 days 

---

## Version 3.0 – Organization-Specific Model Fine-Tuning

**Goal:** Support fine-tuning LLM models for specific organizations.

Planned changes:
- Fine-tunable LLM models
- LoRA-based fine-tuning with Unsloth
- Organization-specific model variants


*Timeline:* 5-10 days 

---

### Version 3.1 – Fine-Tuning Interface

**Goal:** Provide a UI for managing model fine-tuning workflows.

Planned changes:
- UI for exploring fine-tuning workflows
- Ability to switch between model history versions
- SQL interface for viewing reported hallucinations and model bug data

*Timeline:* 2-3 days 
