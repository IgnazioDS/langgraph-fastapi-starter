"""Test configuration and shared fixtures.

Tests require a running PostgreSQL instance. Set TEST_DATABASE_URL or ensure
the default connection (localhost:5432/agentdb_test) is available.

Run: make test (after make up and make migrate)
"""

import os
from collections.abc import AsyncGenerator, Generator
from unittest.mock import MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

# Use a separate test database if TEST_DATABASE_URL is set,
# otherwise fall back to the configured database.
TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL")
if TEST_DATABASE_URL:
    os.environ["DATABASE_URL"] = TEST_DATABASE_URL


@pytest.fixture(scope="session")
def _patch_config() -> Generator[None, None, None]:
    """Ensure required env vars are present for tests."""
    env_defaults = {
        "OPENAI_API_KEY": os.environ.get("OPENAI_API_KEY", "sk-test-not-real"),
        "POSTGRES_PASSWORD": os.environ.get("POSTGRES_PASSWORD", "localdev"),
    }
    with patch.dict(os.environ, env_defaults, clear=False):
        yield


@pytest.fixture(scope="session")
async def client(_patch_config: None) -> AsyncGenerator[AsyncClient, None]:
    """Session-scoped async HTTP client wired to the FastAPI app."""
    from app.main import create_app

    application = create_app()
    async with AsyncClient(
        transport=ASGITransport(app=application), base_url="http://test"
    ) as ac:
        yield ac


@pytest.fixture
async def admin_key(client: AsyncClient) -> str:
    """Create a fresh admin key for a test and return the plaintext."""
    # Bootstrap: we need one key to create more keys.
    # For the first key, call the service directly (bypasses auth middleware).
    from app.services.api_key_service import ApiKeyService

    service = ApiKeyService()
    plaintext, _ = service.create_key(
        name="test-admin", role="admin", tenant_id="default"
    )
    return plaintext


@pytest.fixture
def admin_key_header(admin_key: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {admin_key}"}


@pytest.fixture
async def user_key(client: AsyncClient, admin_key_header: dict[str, str]) -> str:
    """Create a fresh user key via the API and return the plaintext."""
    resp = await client.post(
        "/v1/keys",
        json={"name": "test-user", "role": "user"},
        headers=admin_key_header,
    )
    assert resp.status_code == 201
    return str(resp.json()["key"])


@pytest.fixture
def user_key_header(user_key: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {user_key}"}


@pytest.fixture
def mock_openai() -> Generator[MagicMock, None, None]:
    """Patch ChatOpenAI so tests don't make real LLM calls."""
    from langchain_core.messages import AIMessage

    mock_response = AIMessage(content="Mocked agent response for testing.")
    mock_response.usage_metadata = {"input_tokens": 10, "output_tokens": 5}

    mock_llm = MagicMock()
    mock_llm.bind_tools.return_value = mock_llm
    mock_llm.invoke.return_value = mock_response

    with patch("app.graph.nodes.ChatOpenAI", return_value=mock_llm):
        yield mock_llm
