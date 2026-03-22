# supabase_sessions.py
# Persistent session storage backed by Supabase.
# Table: sessions (session_id text PK, messages jsonb, updated_at timestamptz)

import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

_client = create_client(
    os.environ["SUPABASE_URL"],
    os.environ["SUPABASE_ANON_KEY"],
)


def get_session(session_id: str) -> list:
    """Return the messages list for session_id, or [] if not found."""
    response = (
        _client.table("sessions")
        .select("messages")
        .eq("session_id", session_id)
        .execute()
    )
    if response.data:
        return response.data[0]["messages"]
    return []


def save_session(session_id: str, messages: list) -> None:
    """Upsert the session row with the latest messages list."""
    _client.table("sessions").upsert(
        {
            "session_id": session_id,
            "messages": messages,
            "updated_at": "now()",
        }
    ).execute()
