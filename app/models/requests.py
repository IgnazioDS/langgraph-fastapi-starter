from typing import Literal

from pydantic import BaseModel, Field


class RunAgentRequest(BaseModel):
    session_id: str = Field(..., min_length=1, max_length=255)
    message: str = Field(..., min_length=1, max_length=10000)
    stream: bool = False


class CreateApiKeyRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    role: Literal["user", "admin"] = "user"
    tenant_id: str = Field(default="default", min_length=1, max_length=100)
