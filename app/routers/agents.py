# EXTENSION POINT: Add new agent endpoints here.
# Follow the pattern: validate input → call service → handle errors → return typed response.
# Add new request/response models to app/models/ before adding endpoints.
#
# To support multiple graphs, pass a graph_name param and select in AgentService.

import logging

from fastapi import APIRouter, Depends, HTTPException, Request

from app.graph.graph import get_graph
from app.models.requests import RunAgentRequest
from app.models.responses import ErrorResponse, RunAgentResponse, SessionResponse
from app.services.agent_service import AgentService

router = APIRouter(tags=["agents"])
logger = logging.getLogger(__name__)


def get_agent_service() -> AgentService:
    """FastAPI dependency that returns an AgentService bound to the compiled graph."""
    return AgentService(get_graph())


@router.post("/v1/agent/run", response_model=RunAgentResponse)
async def run_agent(
    request: RunAgentRequest,
    http_request: Request,
    agent_service: AgentService = Depends(get_agent_service),
) -> RunAgentResponse:
    """Run the agent for a single conversational turn.

    The session_id groups messages into a conversation. Use the same session_id
    across calls to maintain context. Conversations are tenant-isolated.
    """
    tenant_id: str = http_request.state.tenant_id
    request_id = getattr(http_request.state, "request_id", None)
    try:
        return await agent_service.run(
            session_id=request.session_id,
            tenant_id=tenant_id,
            message=request.message,
        )
    except Exception as e:
        logger.error(
            "agent_run_failed",
            extra={"request_id": request_id, "error": str(e)},
        )
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                code="AGENT_ERROR",
                message="Agent execution failed.",
                request_id=request_id,
            ).model_dump(),
        )


@router.get("/v1/agent/sessions/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    http_request: Request,
    agent_service: AgentService = Depends(get_agent_service),
) -> SessionResponse:
    """Retrieve a session's message history."""
    tenant_id: str = http_request.state.tenant_id
    request_id = getattr(http_request.state, "request_id", None)
    try:
        session = await agent_service.get_session(session_id, tenant_id)
        if session is None:
            raise HTTPException(
                status_code=404,
                detail=ErrorResponse(
                    code="SESSION_NOT_FOUND",
                    message=f"Session {session_id} not found.",
                    request_id=request_id,
                ).model_dump(),
            )
        return session
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "get_session_failed",
            extra={"request_id": request_id, "session_id": session_id, "error": str(e)},
        )
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                code="SESSION_ERROR",
                message="Failed to retrieve session.",
                request_id=request_id,
            ).model_dump(),
        )
