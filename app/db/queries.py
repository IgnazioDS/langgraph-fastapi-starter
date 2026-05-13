# Raw SQL as module-level string constants.
# Named parameters use %(name)s syntax (psycopg2).
# No f-strings. No string concatenation. Every query is parameterized.
#
# EXTENSION POINT: Add new queries here when adding database tables.
# Follow the pattern: one constant per SQL statement, UPPER_SNAKE_CASE name.
# Use %(param_name)s for all user-supplied values — never interpolate directly.

# ─── API Keys ─────────────────────────────────────────────────────────────────

CREATE_API_KEY = """
    INSERT INTO api_keys (id, key_hash, lookup_hash, name, tenant_id, role, created_at)
    VALUES (%(id)s, %(key_hash)s, %(lookup_hash)s, %(name)s, %(tenant_id)s, %(role)s, NOW())
    RETURNING id, name, tenant_id, role, created_at
"""

# lookup_hash is sha256(plaintext_key) — deterministic, O(1) lookup.
# key_hash is bcrypt(plaintext_key) — stored for compliance/migration compat.
GET_API_KEY_BY_LOOKUP_HASH = """
    SELECT id, key_hash, lookup_hash, name, tenant_id, role, created_at, last_used_at, revoked_at
    FROM api_keys
    WHERE lookup_hash = %(lookup_hash)s AND revoked_at IS NULL
"""

UPDATE_API_KEY_LAST_USED = """
    UPDATE api_keys SET last_used_at = NOW() WHERE id = %(id)s
"""

REVOKE_API_KEY = """
    UPDATE api_keys SET revoked_at = NOW() WHERE id = %(id)s AND revoked_at IS NULL
    RETURNING id
"""

LIST_API_KEYS = """
    SELECT id, name, tenant_id, role, created_at, last_used_at, revoked_at
    FROM api_keys
    WHERE tenant_id = %(tenant_id)s
    ORDER BY created_at DESC
"""

# ─── Sessions ─────────────────────────────────────────────────────────────────

CREATE_SESSION = """
    INSERT INTO agent_sessions (
        id, session_id, tenant_id, created_at, last_active_at, message_count
    )
    VALUES (%(id)s, %(session_id)s, %(tenant_id)s, NOW(), NOW(), 0)
    ON CONFLICT (session_id, tenant_id) DO UPDATE SET last_active_at = NOW()
    RETURNING id, session_id, created_at, last_active_at, message_count
"""

GET_SESSION = """
    SELECT id, session_id, tenant_id, created_at, last_active_at, message_count
    FROM agent_sessions
    WHERE session_id = %(session_id)s AND tenant_id = %(tenant_id)s
"""

# ─── Messages ─────────────────────────────────────────────────────────────────

INSERT_MESSAGE = """
    INSERT INTO agent_messages (id, session_id, role, content, metadata, created_at)
    VALUES (%(id)s, %(session_id)s, %(role)s, %(content)s, %(metadata)s, NOW())
"""

GET_SESSION_MESSAGES = """
    SELECT id, session_id, role, content, metadata, created_at
    FROM agent_messages
    WHERE session_id = %(session_id)s
    ORDER BY created_at ASC
"""

INCREMENT_SESSION_MESSAGE_COUNT = """
    UPDATE agent_sessions
    SET message_count = message_count + 1, last_active_at = NOW()
    WHERE session_id = %(session_id)s
"""
