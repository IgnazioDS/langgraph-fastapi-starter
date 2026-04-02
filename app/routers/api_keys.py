# EXTENSION POINT: Add new key-management endpoints here.
# Follow the pattern: validate input → call service → handle errors → return typed response.
# All endpoints in this router require admin role (enforced by AuthMiddleware).

import logging

from fastapi import APIRouter, HTTPException, Request

from app.models.requests import CreateApiKeyRequest
from app.models.responses import ApiKeyCreatedResponse, ApiKeyResponse, ErrorResponse
from app.services.api_key_service import api_key_service

router = APIRouter(tags=["api-keys"])
logger = logging.getLogger(__name__)


@router.post("/v1/keys", response_model=ApiKeyCreatedResponse, status_code=201)
async def create_api_key(
    request: CreateApiKeyRequest,
    http_request: Request,
) -> ApiKeyCreatedResponse:
    """Create a new API key. Returns the plaintext key once — it cannot be recovered."""
    request_id = getattr(http_request.state, "request_id", None)
    try:
        _plaintext, response = api_key_service.create_key(
            name=request.name,
            role=request.role,
            tenant_id=request.tenant_id,
        )
        # Inject the plaintext key into the response before returning
        return ApiKeyCreatedResponse(
            id=response.id,
            key=_plaintext,
            name=response.name,
            role=response.role,
            tenant_id=response.tenant_id,
            created_at=response.created_at,
        )
    except Exception as e:
        logger.error("create_key_failed", extra={"request_id": request_id, "error": str(e)})
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                code="KEY_CREATION_ERROR",
                message="Failed to create API key.",
                request_id=request_id,
            ).model_dump(),
        )


@router.delete("/v1/keys/{key_id}", status_code=204)
async def revoke_api_key(
    key_id: str,
    http_request: Request,
) -> None:
    """Revoke an API key. The key immediately stops working."""
    request_id = getattr(http_request.state, "request_id", None)
    tenant_id: str = http_request.state.tenant_id
    try:
        revoked = api_key_service.revoke_key(key_id, tenant_id)
        if not revoked:
            raise HTTPException(
                status_code=404,
                detail=ErrorResponse(
                    code="KEY_NOT_FOUND",
                    message=f"Key {key_id} not found or already revoked.",
                    request_id=request_id,
                ).model_dump(),
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("revoke_key_failed", extra={"request_id": request_id, "error": str(e)})
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                code="KEY_REVOCATION_ERROR",
                message="Failed to revoke API key.",
                request_id=request_id,
            ).model_dump(),
        )


@router.get("/v1/keys", response_model=list[ApiKeyResponse])
async def list_api_keys(
    http_request: Request,
) -> list[ApiKeyResponse]:
    """List all API keys for the current tenant."""
    request_id = getattr(http_request.state, "request_id", None)
    tenant_id: str = http_request.state.tenant_id
    try:
        return api_key_service.list_keys(tenant_id)
    except Exception as e:
        logger.error("list_keys_failed", extra={"request_id": request_id, "error": str(e)})
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                code="KEY_LIST_ERROR",
                message="Failed to list API keys.",
                request_id=request_id,
            ).model_dump(),
        )
