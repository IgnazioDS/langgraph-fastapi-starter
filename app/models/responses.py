from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class TokenUsage(BaseModel):
    input_tokens: int
    output_tokens: int


class RunAgentResponse(BaseModel):
    session_id: str
    response: str
    run_id: str
    usage: TokenUsage


class ApiKeyCreatedResponse(BaseModel):
    id: str
    key: str          # Plaintext — returned once only
    name: str
    role: str
    tenant_id: str
    created_at: datetime


class ApiKeyResponse(BaseModel):
    id: str
    name: str
    role: str
    tenant_id: str
    created_at: datetime
    last_used_at: datetime | None
    revoked_at: datetime | None


class MessageResponse(BaseModel):
    role: str
    content: str
    created_at: datetime


class SessionResponse(BaseModel):
    session_id: str
    message_count: int
    created_at: datetime
    last_active_at: datetime
    messages: list[MessageResponse]


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded", "down"]
    version: str


class DetailedHealthResponse(BaseModel):
    status: Literal["ok", "degraded", "down"]
    version: str
    database: Literal["ok", "error"]
    graph: Literal["ok", "error"]
    checks: dict[str, str]


class ErrorResponse(BaseModel):
    code: str
    message: str
    request_id: str | None = None
