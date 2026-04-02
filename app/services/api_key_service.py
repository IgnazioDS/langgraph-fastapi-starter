import hashlib
import secrets
import uuid
from dataclasses import dataclass
from datetime import datetime

import bcrypt

from app.db.connection import db_conn
from app.db.queries import (
    CREATE_API_KEY,
    GET_API_KEY_BY_LOOKUP_HASH,
    LIST_API_KEYS,
    REVOKE_API_KEY,
    UPDATE_API_KEY_LAST_USED,
)
from app.models.responses import ApiKeyCreatedResponse, ApiKeyResponse


@dataclass
class ValidatedKey:
    """Minimal representation of a validated API key for use in request state."""

    id: str
    name: str
    tenant_id: str
    role: str


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def _bcrypt_hash(value: str) -> str:
    return bcrypt.hashpw(value.encode(), bcrypt.gensalt(rounds=12)).decode()


class ApiKeyService:
    def create_key(
        self, name: str, role: str, tenant_id: str
    ) -> tuple[str, ApiKeyCreatedResponse]:
        """Generate a new API key, persist it, and return (plaintext_key, response).

        The plaintext key is returned exactly once. After this call it is unrecoverable.
        """
        plaintext = "sk-" + secrets.token_hex(32)
        key_hash = _bcrypt_hash(plaintext)
        lookup_hash = _sha256(plaintext)
        key_id = str(uuid.uuid4())

        with db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    CREATE_API_KEY,
                    {
                        "id": key_id,
                        "key_hash": key_hash,
                        "lookup_hash": lookup_hash,
                        "name": name,
                        "tenant_id": tenant_id,
                        "role": role,
                    },
                )
                row = cur.fetchone()

        if row is None:
            raise RuntimeError("Key creation returned no row")

        created_id, created_name, created_tenant, created_role, created_at = row
        return plaintext, ApiKeyCreatedResponse(
            id=str(created_id),
            key=plaintext,
            name=created_name,
            role=created_role,
            tenant_id=created_tenant,
            created_at=created_at,
        )

    def validate_key(self, plaintext_key: str) -> ValidatedKey | None:
        """Validate a plaintext API key.

        Strategy: sha256(key) for O(1) database lookup, then update last_used_at.
        The bcrypt hash is stored for compliance/migration compat but not used for lookup.
        """
        lookup_hash = _sha256(plaintext_key)

        with db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    GET_API_KEY_BY_LOOKUP_HASH,
                    {"lookup_hash": lookup_hash},
                )
                row = cur.fetchone()

            if row is None:
                return None

            key_id, _key_hash, _lookup_hash, name, tenant_id, role, *_ = row

            with conn.cursor() as cur:
                cur.execute(UPDATE_API_KEY_LAST_USED, {"id": str(key_id)})

        return ValidatedKey(
            id=str(key_id),
            name=name,
            tenant_id=tenant_id,
            role=role,
        )

    def revoke_key(self, key_id: str, tenant_id: str) -> bool:
        """Revoke a key by UUID. Returns True if revoked, False if not found or already revoked."""
        with db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(REVOKE_API_KEY, {"id": key_id})
                row = cur.fetchone()
        return row is not None

    def list_keys(self, tenant_id: str) -> list[ApiKeyResponse]:
        """List all (non-revoked and revoked) keys for a tenant, ordered by created_at desc."""
        with db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(LIST_API_KEYS, {"tenant_id": tenant_id})
                rows = cur.fetchall()

        results = []
        for row in rows:
            key_id, name, t_id, role, created_at, last_used_at, revoked_at = row
            results.append(
                ApiKeyResponse(
                    id=str(key_id),
                    name=name,
                    role=role,
                    tenant_id=t_id,
                    created_at=created_at,
                    last_used_at=last_used_at,
                    revoked_at=revoked_at,
                )
            )
        return results


# Module-level singleton used by middleware and routers via dependency injection.
api_key_service = ApiKeyService()
