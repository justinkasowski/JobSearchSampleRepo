# Deployment Guide

This document describes how to deploy the RAG LLM system to Google Cloud using the existing infrastructure defined in this repository.

The production environment consists of:

- Google Cloud Run
- Google Cloud SQL (PostgreSQL)
- Ollama running inside the application container
- Firebase Authentication
- Slack / Discord integrations
- Optional Cloud Storage for document corpora

---

# Overview

Deployment is handled automatically through **Cloud Build** when changes are pushed to the repository.

Deployment flow:

```
GitHub Push
↓
Cloud Build
↓
Docker Image Build
↓
Artifact Registry
↓
Cloud Run Deployment
```

---

# Required Cloud Resources

Before deployment the following resources must exist:

- Cloud Run service
- Cloud SQL PostgreSQL instance
- Artifact Registry repository
- Firebase project
- Slack / Discord webhooks
- Optional: Cloud Storage bucket for PDFs

---

# Required Environment Variables

The application expects the following environment variables.

Core configuration:

```
OLLAMA_MODEL
OLLAMA_KEEP_ALIVE
DB_NAME
INSTANCE_CONNECTION_NAME
```

Database authentication:

```
DB_PASS
```

Firebase authentication:

```
FIREBASE_SERVICE_ACCOUNT
```

Integration webhooks:

```
SLACK_WEBHOOK_POLICY
SLACK_WEBHOOK_HR
SLACK_WEBHOOK_SALES
SLACK_WEBHOOK_HEALTHCHECK

DISCORD_WEBHOOK_POLICY
DISCORD_WEBHOOK_HR
DISCORD_WEBHOOK_SALES
```

Vector storage (if pgvector is enabled):

```
PGVECTOR_CONNECTION_STRING
```

Optional document storage:

```
PDF_GCS_BUCKET
```

---

# Build and Deploy Process

Deployment is triggered automatically through **Cloud Build**.

The build pipeline performs:

```
docker build
↓
push image to Artifact Registry
↓
deploy to Cloud Run
```

Cloud Build configuration is defined in:

```
cloudbuild.yaml
```

---

# Manual Deployment

To deploy manually:

```
gcloud builds submit
```

Or deploy a specific image:

```
gcloud run deploy jobsearchsamplerepo \
--image <IMAGE_URL> \
--region us-east4 \
--platform managed
```

---

# Domain Configuration

The service can be mapped to custom domains.

Example domains:

```
rag-demo.justinkasowski.com
ragdemo.justinkasowski.com
```

DNS should point to:

```
ghs.googlehosted.com
```

Cloud Run automatically provisions SSL certificates after DNS propagation.

---

# Monitoring

Health checks are available at:

```
GET /health
```

Optional global monitoring endpoint:

```
GET /globalHealthCheck
```

This endpoint can post status messages to Slack.

---

# Scaling

Cloud Run automatically scales based on incoming traffic.

Configuration options include:

- minimum instances
- maximum instances
- concurrency
- memory / CPU allocation

---

# Deployment Checklist

Before deploying ensure:

- Cloud SQL instance is reachable
- environment variables are configured
- Firebase authentication domains are authorized
- Slack / Discord webhooks are set
- DNS is configured for custom domains

---

# Summary

Production deployment uses:

```
Cloud Run
↓
Cloud SQL
↓
Ollama LLM
↓
RAG retrieval
↓
external integrations
```

The entire process is automated through Cloud Build.