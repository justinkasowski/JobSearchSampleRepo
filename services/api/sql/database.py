from sqlalchemy import create_engine, text

from config import LOCAL_RUN, DB_USER, DB_PASS, DB_NAME, INSTANCE_CONNECTION_NAME, DB_HOST, DB_PORT

if LOCAL_RUN:
    DATABASE_URL = f"postgresql+pg8000://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
else:
    DATABASE_URL = (
        f"postgresql+pg8000://{DB_USER}:{DB_PASS}@/{DB_NAME}"
        f"?unix_sock=/cloudsql/{INSTANCE_CONNECTION_NAME}/.s.PGSQL.5432"
    )

print(f"DATABASE_URL={DATABASE_URL}")
print(f"Connecting to postgres at {DB_HOST}:{DB_PORT} db={DB_NAME} local_run={LOCAL_RUN}")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)

def init_db():
    with engine.begin() as conn:
        print(conn.execute(text("select current_database()")).scalar())
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))

        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS bug_reports (
            id BIGSERIAL PRIMARY KEY,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            user_uid TEXT,
            question TEXT,
            answer TEXT,
            integration_type TEXT,
            llm_plan_integration TEXT,
            integration_channel TEXT,
            llm_plan_channel TEXT,
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

        conn.execute(text("""
        ALTER TABLE bug_reports
        ADD COLUMN IF NOT EXISTS llm_plan_integration TEXT;
        """))

        conn.execute(text("""
        ALTER TABLE bug_reports
        ADD COLUMN IF NOT EXISTS llm_plan_channel TEXT;
        """))