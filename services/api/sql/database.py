import os
from sqlalchemy import create_engine
from sqlalchemy import text

DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_NAME = os.getenv("DB_NAME")
INSTANCE_CONNECTION_NAME = os.getenv("INSTANCE_CONNECTION_NAME")

engine = create_engine(
    f"postgresql+pg8000://{DB_USER}:{DB_PASS}@/{DB_NAME}"
    f"?unix_sock=/cloudsql/{INSTANCE_CONNECTION_NAME}/.s.PGSQL.5432"
)

def init_db():
    with engine.begin() as conn:
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS bug_reports (
            id BIGSERIAL PRIMARY KEY,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            user_uid TEXT,
            question TEXT,
            answer TEXT,
            integration_type TEXT,
            integration_channel TEXT,
            integration_rationale TEXT,
            integration_json JSONB,
            rag_json JSONB,
            report_text TEXT,
            status TEXT NOT NULL DEFAULT 'open'
        );
        """))