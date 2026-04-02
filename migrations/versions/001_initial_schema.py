"""Initial schema: api_keys, agent_sessions, agent_messages

Revision ID: 001
Revises:
Create Date: 2026-04-02

Extensions enabled: vector (pgvector), uuid-ossp
"""
from typing import Sequence, Union

from alembic import op

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

    # API key storage.
    # key_hash: bcrypt hash — stored for compliance, NOT used for lookup.
    # lookup_hash: sha256 hash — deterministic, used for O(1) SELECT WHERE lookup_hash = ?
    # See app/services/api_key_service.py for the two-hash strategy rationale.
    op.execute("""
        CREATE TABLE api_keys (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            key_hash TEXT NOT NULL UNIQUE,
            lookup_hash TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            tenant_id TEXT NOT NULL DEFAULT 'default',
            role TEXT NOT NULL DEFAULT 'user',
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            last_used_at TIMESTAMPTZ,
            revoked_at TIMESTAMPTZ
        )
    """)
    op.execute("CREATE INDEX api_keys_tenant_idx ON api_keys (tenant_id)")
    op.execute(
        "CREATE INDEX api_keys_lookup_idx ON api_keys (lookup_hash) WHERE revoked_at IS NULL"
    )

    # Agent session tracking. One session per (session_id, tenant_id) pair.
    # EXTENSION POINT: Add columns here if you need per-session metadata
    # (e.g., agent_type, user_id, custom_metadata JSONB).
    op.execute("""
        CREATE TABLE agent_sessions (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            session_id TEXT NOT NULL,
            tenant_id TEXT NOT NULL DEFAULT 'default',
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            last_active_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            message_count INTEGER NOT NULL DEFAULT 0,
            UNIQUE (session_id, tenant_id)
        )
    """)
    op.execute("CREATE INDEX sessions_tenant_idx ON agent_sessions (tenant_id)")
    op.execute("CREATE INDEX sessions_session_id_idx ON agent_sessions (session_id)")

    # Message history per session.
    # role: 'user' | 'assistant' | 'tool'
    # metadata: arbitrary JSON for run_id, tool names, latency, etc.
    op.execute("""
        CREATE TABLE agent_messages (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            metadata JSONB DEFAULT '{}',
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)
    op.execute("CREATE INDEX messages_session_idx ON agent_messages (session_id)")
    op.execute(
        "CREATE INDEX messages_created_idx ON agent_messages (session_id, created_at)"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS agent_messages")
    op.execute("DROP TABLE IF EXISTS agent_sessions")
    op.execute("DROP TABLE IF EXISTS api_keys")
    # Extensions are not dropped on downgrade — they may be used by other migrations.
