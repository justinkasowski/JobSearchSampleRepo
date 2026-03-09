import os
from sqlalchemy import create_engine
from sqlalchemy import text

from config import LOCAL_RUN, DB_USER, DB_PASS, DB_NAME, INSTANCE_CONNECTION_NAME


engine = create_engine(
    (
        f"postgresql+pg8000://{DB_USER}:{DB_PASS}@/{DB_NAME}"
        f"?unix_sock=/cloudsql/{INSTANCE_CONNECTION_NAME}/.s.PGSQL.5432"
    )
    if not LOCAL_RUN
    else f"postgresql+pg8000://{DB_USER}:{DB_PASS}@host.docker.internal:5432/{DB_NAME}"
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
            report_type TEXT NOT NULL DEFAULT 'bug',
            manual_review_appropriate BOOLEAN,
            manual_review_note TEXT,
            status TEXT NOT NULL DEFAULT 'open'
        );
        """))

        conn.execute(text("""
        ALTER TABLE bug_reports
        ADD COLUMN IF NOT EXISTS report_type TEXT NOT NULL DEFAULT 'bug';
        """))

        conn.execute(text("""
        ALTER TABLE bug_reports
        ADD COLUMN IF NOT EXISTS manual_review_appropriate BOOLEAN;
        """))

        conn.execute(text("""
        ALTER TABLE bug_reports
        ADD COLUMN IF NOT EXISTS manual_review_note TEXT;
        """))