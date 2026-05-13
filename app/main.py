import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from app.config import config
from app.db.connection import close_pool, init_pool
from app.graph.graph import init_graph
from app.middleware.auth import AuthMiddleware
from app.middleware.logging import LoggingMiddleware, _setup_logging
from app.models.responses import ErrorResponse
from app.routers.agents import router as agents_router
from app.routers.api_keys import router as keys_router
from app.routers.health import router as health_router

APP_VERSION = "0.1.0"

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    _setup_logging()
    logger.info("starting_up", extra={"version": APP_VERSION, "env": config.app_env})
    init_pool()
    init_graph()
    logger.info("startup_complete")

    yield

    logger.info("shutting_down")
    close_pool()
    logger.info("shutdown_complete")


def create_app() -> FastAPI:
    app = FastAPI(
        title="LangGraph FastAPI Starter",
        version=APP_VERSION,
        docs_url=None if config.is_production else "/docs",
        redoc_url=None if config.is_production else "/redoc",
        lifespan=lifespan,
    )

    # Middleware runs in reverse registration order.
    # LoggingMiddleware must be outermost (registered last) so it wraps everything.
    app.add_middleware(AuthMiddleware)
    app.add_middleware(LoggingMiddleware)

    app.include_router(health_router)
    app.include_router(agents_router)
    app.include_router(keys_router)

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        if isinstance(exc.detail, dict):
            return JSONResponse(status_code=exc.status_code, content=exc.detail)

        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                code="HTTP_ERROR",
                message=str(exc.detail),
                request_id=getattr(request.state, "request_id", None),
            ).model_dump(),
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.error(
            "unhandled_exception",
            extra={"error": str(exc), "type": type(exc).__name__},
        )
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                code="INTERNAL_ERROR",
                message="An unexpected error occurred.",
                request_id=getattr(request.state, "request_id", None),
            ).model_dump(),
        )

    return app


app = create_app()
