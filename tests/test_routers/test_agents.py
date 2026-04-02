import pytest
from httpx import AsyncClient
from unittest.mock import MagicMock


@pytest.mark.asyncio
async def test_run_agent_returns_response(
    client: AsyncClient,
    user_key_header: dict[str, str],
    mock_openai: MagicMock,
) -> None:
    response = await client.post(
        "/v1/agent/run",
        json={"session_id": "test-session-1", "message": "Hello"},
        headers=user_key_header,
    )
    assert response.status_code == 200
    body = response.json()
    assert "response" in body
    assert isinstance(body["response"], str)
    assert len(body["response"]) > 0
    assert body["session_id"] == "test-session-1"
    assert "run_id" in body
    assert body["run_id"].startswith("run_")
    assert "usage" in body
    assert isinstance(body["usage"]["input_tokens"], int)
    assert isinstance(body["usage"]["output_tokens"], int)


@pytest.mark.asyncio
async def test_session_persists_across_runs(
    client: AsyncClient,
    user_key_header: dict[str, str],
    mock_openai: MagicMock,
) -> None:
    session_id = "test-persistence-session"

    await client.post(
        "/v1/agent/run",
        json={"session_id": session_id, "message": "My name is Alex"},
        headers=user_key_header,
    )

    session_resp = await client.get(
        f"/v1/agent/sessions/{session_id}",
        headers=user_key_header,
    )
    assert session_resp.status_code == 200
    body = session_resp.json()
    assert body["session_id"] == session_id
    assert body["message_count"] >= 2  # user + assistant


@pytest.mark.asyncio
async def test_missing_session_returns_404(
    client: AsyncClient, user_key_header: dict[str, str]
) -> None:
    response = await client.get(
        "/v1/agent/sessions/nonexistent-xyz-abc-123",
        headers=user_key_header,
    )
    assert response.status_code == 404
    assert response.json()["code"] == "SESSION_NOT_FOUND"


@pytest.mark.asyncio
async def test_run_agent_requires_auth(client: AsyncClient) -> None:
    response = await client.post(
        "/v1/agent/run",
        json={"session_id": "s1", "message": "Hello"},
    )
    assert response.status_code == 401
    assert response.json()["code"] == "MISSING_API_KEY"
