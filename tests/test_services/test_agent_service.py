from unittest.mock import MagicMock, patch

import pytest
from langchain_core.messages import AIMessage

from app.services.agent_service import AgentService


@pytest.mark.asyncio
async def test_run_returns_response_with_correct_shape(_patch_config: None) -> None:
    """AgentService.run() returns a RunAgentResponse with all required fields."""
    mock_response = AIMessage(content="Test response")
    mock_response.usage_metadata = {"input_tokens": 5, "output_tokens": 10}

    mock_graph = MagicMock()
    mock_graph.invoke.return_value = {
        "messages": [mock_response],
        "session_id": "s1",
        "tenant_id": "default",
        "context": [],
        "run_id": "run_test",
        "input_tokens": 5,
        "output_tokens": 10,
    }

    with patch("app.graph.nodes.ChatOpenAI"):
        service = AgentService(mock_graph)
        result = await service.run(
            session_id="svc-test-session",
            tenant_id="default",
            message="Hello",
        )

    assert result.session_id == "svc-test-session"
    assert result.response == "Test response"
    assert result.run_id.startswith("run_")
    assert result.usage.input_tokens == 5
    assert result.usage.output_tokens == 10


@pytest.mark.asyncio
async def test_get_session_returns_none_for_missing(_patch_config: None) -> None:
    mock_graph = MagicMock()
    service = AgentService(mock_graph)
    result = await service.get_session("nonexistent-session-xyz", "default")
    assert result is None
