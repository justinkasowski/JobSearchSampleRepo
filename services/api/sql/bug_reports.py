from sqlalchemy import text
from .database import engine

def insert_integration_bug_report(payload):
    with engine.begin() as conn:
        conn.execute(
            text("""
            INSERT INTO bug_reports (
                user_uid,
                question,
                answer,
                integration_type,
                integration_channel,
                integration_rationale,
                integration_json,
                rag_json,
                report_text,
                report_type,
                manual_review_appropriate,
                manual_review_note
            ) VALUES (
                :user_uid,
                :question,
                :answer,
                :integration_type,
                :integration_channel,
                :integration_rationale,
                CAST(:integration_json AS JSONB),
                CAST(:rag_json AS JSONB),
                :report_text,
                :report_type,
                :manual_review_appropriate,
                :manual_review_note
            )
            """),
            payload,
        )