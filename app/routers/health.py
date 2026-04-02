import logging

from fastapi import APIRouter

from app.db.connection import db_conn
from app.graph.graph import get_graph
from app.models.responses import DetailedHealthResponse, HealthResponse

router = APIRouter(tags=["health"])
logger = logging.getLogger(__name__)

# Imported and set by main.py at startup
APP_VERSION = "0.1.0"


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Liveness probe. Returns 200 as long as the process is running."""
    return HealthResponse(status="ok", version=APP_VERSION)


@router.get("/health/detailed", response_model=DetailedHealthResponse)
async def detailed_health() -> DetailedHealthResponse:
    """Readiness probe. Checks database connectivity and graph initialization."""
    checks: dict[str, str] = {}
    db_status: str
    graph_status: str

    try:
        with db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
        db_status = "ok"
        checks["database"] = "SELECT 1 succeeded"
    except Exception as e:
        db_status = "error"
        checks["database"] = str(e)
        logger.error("health_check_db_failed", extra={"error": str(e)})

    try:
        get_graph()
        graph_status = "ok"
        checks["graph"] = "compiled and ready"
    except Exception as e:
        graph_status = "error"
        checks["graph"] = str(e)
        logger.error("health_check_graph_failed", extra={"error": str(e)})

    overall = "ok" if db_status == "ok" and graph_status == "ok" else "degraded"

    return DetailedHealthResponse(
        status=overall,  # type: ignore[arg-type]
        version=APP_VERSION,
        database=db_status,  # type: ignore[arg-type]
        graph=graph_status,  # type: ignore[arg-type]
        checks=checks,
    )
