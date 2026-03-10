#region imports
import json
from pathlib import Path
from typing import Optional

import firebase_admin
import requests
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from firebase_admin import auth
from google.cloud import firestore
from google.cloud.firestore_v1 import Increment
from pydantic import BaseModel

from config import AVAILABLE_CORPORA, MODEL, OLLAMA_KEEP_ALIVE, OLLAMA_URL, LOCAL_RUN, DB_USER, DB_NAME, DB_HOST, \
    DB_PORT
from integrations.integrations_handler import plan_message, send_message
from integrations.schemas import SendMessageRequest, SendMessageResponse, IntegrationPlanRequest, MessagePlan
from rag.ingest import ingest_corpus
from rag.retrieve import corpus_has_documents, rag_answer
from sql.bug_reports import insert_integration_bug_report
from sql.database import init_db

#endregion

QUERY_LIMIT = 100

db = None
if not LOCAL_RUN:
    firebase_admin.initialize_app()
    db = firestore.Client()
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")


#region Class definitions
class IngestRequest(BaseModel):
    corpus: str
    clean_rebuild: bool = False

class PromptRequest(BaseModel):
    prompt: str
    keep_alive: Optional[str] = None

class DirectQueryResponse(BaseModel):
    model: str
    response: str
    prompt: str

class QueryRequest(BaseModel):
    corpus: str
    question: str
    k: int = 4
    section: Optional[str] = None
    document_type: Optional[str] = None
    keep_alive: Optional[str] = None

class BugReportRequest(BaseModel):
    question: Optional[str] = None
    answer: Optional[str] = None
    integration_type: Optional[str] = None
    llm_plan_integration: Optional[str] = None
    integration_channel: Optional[str] = None
    llm_plan_channel: Optional[str] = None
    integration_rationale: Optional[str] = None
    integration_json: Optional[dict] = None
    rag_json: Optional[dict] = None
    report_text: Optional[str] = None
    report_type: Optional[str] = None
    manual_review_appropriate: Optional[bool] = None
    manual_review_note: Optional[str] = None
#endregion


#region Startup

@app.on_event("startup")
def startup():
    # if not LOCAL_RUN:
        try:
            print("init_db")
            print(f"LOCAL_RUN={LOCAL_RUN}")
            print(f"DB_USER={DB_USER}")
            print(f"DB_NAME={DB_NAME}")
            print(f"DB_HOST={DB_HOST}")
            print(f"DB_PORT={DB_PORT}")
            init_db()
            print("success")
        except Exception as e:
            print(f"Database init failed: {e}")


@app.get("/", response_class=HTMLResponse)
def home():
    html = Path("static/index.html").read_text()
    html = html.replace("__LOCAL_RUN__", str(LOCAL_RUN).lower())
    return HTMLResponse(html)


def check_ollama(model: str, keep_alive: str | None = None) -> dict:
    try:
        r = requests.post(
            OLLAMA_URL,
            json={
                "model": model,
                "prompt": "",
                "stream": False,
                "keep_alive": keep_alive or OLLAMA_KEEP_ALIVE,
            },
            timeout=300,
        )
        r.raise_for_status()
        data = r.json()

        return {
            "ok": True,
            "model": model,
            "ollama_url": OLLAMA_URL,
            "response_preview": (data.get("response", "") or "").strip()[:80],
        }
    except Exception as e:
        return {
            "ok": False,
            "model": model,
            "ollama_url": OLLAMA_URL,
            "error": str(e),
        }


@app.post("/warmup")
def warmup():
    result = check_ollama(MODEL, OLLAMA_KEEP_ALIVE)

    if not result["ok"]:
        raise HTTPException(
            status_code=503,
            detail=f"Ollama warmup failed: {result['error']}"
        )

    return {
        "status": "warmed",
        "model": MODEL,
        "ollama_url": OLLAMA_URL,
    }


@app.get("/health")
def health():
    result = check_ollama(MODEL, OLLAMA_KEEP_ALIVE)

    if not result["ok"]:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "error",
                "model": MODEL,
                "ollama_url": OLLAMA_URL,
                "corpora": AVAILABLE_CORPORA,
                "error": result["error"],
            },
        )

    return {
        "status": "ok",
        "model": MODEL,
        "ollama_url": OLLAMA_URL,
        "corpora": AVAILABLE_CORPORA,
    }
#endregion

@app.get("/globalHealthCheck")
def health_check_slack():
    """
    Called by an external scheduler. Writes health result to Slack.
    """
    result = check_ollama(MODEL, OLLAMA_KEEP_ALIVE)

    plan = MessagePlan(
        integrations=["slack"],
        channel="healthcheck",
        requiresReview=False,
        rationale="Automated global health heartbeat."
    )

    if result["ok"]:
        send_message(plan, f"PASS: {MODEL} healthy")
        return {
            "status": "ok",
            "message": "Health check passed and Slack notified"
        }

    send_message(plan, f"FAIL: {MODEL} unhealthy - {result['error']}")
    raise HTTPException(
        status_code=503,
        detail=result["error"]
    )


#region Ingest/Query
@app.get("/rag/status")
def rag_status():
    status = {}

    for corpus in ["hr", "policy", "sales"]:
        try:
            status[corpus] = corpus_has_documents(corpus)
        except Exception:
            status[corpus] = False

    return {"corpus_status": status}

@app.post("/rag/ingest")
def rag_ingest(req: IngestRequest):
    try:
        corpus = req.corpus.strip().lower()

        if corpus == "all":
            results = {}
            for name in AVAILABLE_CORPORA:
                results[name] = ingest_corpus(name, clean_rebuild=req.clean_rebuild)
            return {
                "corpus": "all",
                "clean_rebuild": req.clean_rebuild,
                "results": results,
            }

        return ingest_corpus(corpus, clean_rebuild=req.clean_rebuild)

    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/directQuery", response_model=DirectQueryResponse)
def direct_query(req: PromptRequest, authorization: Optional[str] = Header(None)):
    if not LOCAL_RUN:
        uid = get_uid_from_auth_header(authorization)
        run_count = increment_user_run_count(uid)

        if run_count > 100:
            raise HTTPException(
                status_code=403,
                detail="Users limited to 100 queries, contact Justin (justin.kasowski@gmail.com)"
            )

    r = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL,
            "prompt": req.prompt,
            "stream": False,
            "keep_alive": req.keep_alive or OLLAMA_KEEP_ALIVE,
        },
        timeout=300,
    )
    r.raise_for_status()
    data = r.json()

    response_payload = {
        "model": MODEL,
        "response": data.get("response", "").strip(),
        "prompt": req.prompt,
    }

    return response_payload


@app.post("/rag/query")
def rag_query(req: QueryRequest, authorization: Optional[str] = Header(None)):
    if not LOCAL_RUN:
        uid = get_uid_from_auth_header(authorization)
        run_count = increment_user_run_count(uid)

        if run_count > 100:
            raise HTTPException(
                status_code=403,
                detail="Users limited to 100 queries, contact Justin (justin.kasowski@gmail.com)"
            )

    try:
        corpus = req.corpus.strip().lower()
        auto_ingested = False
        ingest_result = None

        if corpus == "all":
            missing = []
            for name in AVAILABLE_CORPORA:
                if not corpus_has_documents(name):
                    missing.append(name)

            if missing:
                auto_ingested = True
                ingest_result = {}
                for name in missing:
                    ingest_result[name] = ingest_corpus(name, clean_rebuild=False)
        else:
            if not corpus_has_documents(corpus):
                auto_ingested = True
                ingest_result = ingest_corpus(corpus, clean_rebuild=False)

        response_payload = rag_answer(
            corpus=corpus,
            question=req.question,
            k=req.k,
            section=req.section,
            document_type=req.document_type,
            keep_alive=req.keep_alive or OLLAMA_KEEP_ALIVE,
            include_prompt=True,
        )

        response_payload["auto_ingested"] = auto_ingested
        response_payload["ingest_result"] = ingest_result

        return response_payload

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
#endregion


#region Integrations
@app.post("/integrations/plan")
def integrations_plan(req: IntegrationPlanRequest):
    try:
        result = plan_message(
            instruction=req.instruction,
            keep_alive=req.keep_alive or OLLAMA_KEEP_ALIVE,
        )
        return {
            "plan": result["plan"],
            "prompt": result["prompt"],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/integrations/send", response_model=SendMessageResponse)
def integrations_send(req: SendMessageRequest):
    try:
        result = send_message(req.plan, req.message)
        return SendMessageResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/bugs/report")
def report_bug(req: BugReportRequest, authorization: Optional[str] = Header(None)):
    try:
        uid = None
        if not LOCAL_RUN:
            uid = get_uid_from_auth_header(authorization)

        insert_integration_bug_report({
            "user_uid": uid,
            "question": req.question,
            "answer": req.answer,
            "integration_type": req.integration_type,
            "llm_plan_integration": req.llm_plan_integration,
            "integration_channel": req.integration_channel,
            "llm_plan_channel": req.llm_plan_channel,
            "integration_rationale": req.integration_rationale,
            "integration_json": json.dumps(req.integration_json or {}),
            "rag_json": json.dumps(req.rag_json or {}),
            "report_text": req.report_text,
            "report_type": req.report_type,
            "manual_review_appropriate": req.manual_review_appropriate,
            "manual_review_note": req.manual_review_note,
        })

        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
#endregion


#region Helper Functions
def get_uid_from_auth_header(authorization: Optional[str]) -> Optional[str]:
    if LOCAL_RUN:
        return "local-dev-user"

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing auth token")

    token = authorization.split("Bearer ", 1)[1].strip()

    try:
        decoded = auth.verify_id_token(token)
        return decoded["uid"]
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid auth token")


def increment_user_run_count(uid: str) -> int | None:
    if LOCAL_RUN or (db is None):
        return None

    user_ref = db.collection("users").document(uid)
    user_ref.set(
        {
            "run_count": Increment(1),
            "last_run_at": firestore.SERVER_TIMESTAMP,
        },
        merge=True,
    )
    snap = user_ref.get()
    return snap.to_dict().get("run_count", 0)
#endregion
