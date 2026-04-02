# EXTENSION POINT: Replace or extend API key validation here.
# To add OAuth: implement token verification in _validate_bearer_token()
# and set the same request.state fields so downstream routes work unchanged.
# To add JWT: decode and verify here, populate request.state.tenant_id from claims.

import json

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse

from app.models.responses import ErrorResponse
from app.services.api_key_service import api_key_service

# Routes that bypass authentication entirely
_PUBLIC_ROUTES: set[tuple[str, str]] = {
    ("GET", "/health"),
    ("GET", "/docs"),
    ("GET", "/openapi.json"),
    ("GET", "/redoc"),
}

# Routes that require admin role (checked after auth passes)
_ADMIN_ROUTES: set[tuple[str, str]] = {
    ("POST", "/v1/keys"),
}


def _is_admin_route(method: str, path: str) -> bool:
    if (method, path) in _ADMIN_ROUTES:
        return True
    # DELETE /v1/keys/{id}
    if method == "DELETE" and path.startswith("/v1/keys/"):
        return True
    return False


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        method = request.method
        path = request.url.path

        # Skip auth for public routes
        if (method, path) in _PUBLIC_ROUTES:
            return await call_next(request)

        # Extract Bearer token
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content=json.loads(
                    ErrorResponse(
                        code="MISSING_API_KEY",
                        message="Authorization header with Bearer token is required.",
                    ).model_dump_json()
                ),
            )

        token = auth_header[len("Bearer "):]
        validated = api_key_service.validate_key(token)

        if validated is None:
            return JSONResponse(
                status_code=401,
                content=json.loads(
                    ErrorResponse(
                        code="INVALID_API_KEY",
                        message="The provided API key is invalid or has been revoked.",
                    ).model_dump_json()
                ),
            )

        # Attach auth info to request state for downstream use
        request.state.api_key = validated
        request.state.tenant_id = validated.tenant_id

        # Admin-only routes
        if _is_admin_route(method, path) and validated.role != "admin":
            return JSONResponse(
                status_code=403,
                content=json.loads(
                    ErrorResponse(
                        code="INSUFFICIENT_PERMISSIONS",
                        message="This endpoint requires admin role.",
                    ).model_dump_json()
                ),
            )

        return await call_next(request)
