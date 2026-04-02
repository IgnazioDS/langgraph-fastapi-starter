import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_returns_ok(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "version" in body
    assert isinstance(body["version"], str)


@pytest.mark.asyncio
async def test_health_requires_no_auth(client: AsyncClient) -> None:
    """GET /health must return 200 without any Authorization header."""
    response = await client.get("/health")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_detailed_health_returns_checks(
    client: AsyncClient, admin_key_header: dict[str, str]
) -> None:
    response = await client.get("/health/detailed", headers=admin_key_header)
    assert response.status_code == 200
    body = response.json()
    assert "status" in body
    assert "database" in body
    assert "graph" in body
    assert "checks" in body
    assert isinstance(body["checks"], dict)


@pytest.mark.asyncio
async def test_detailed_health_requires_auth(client: AsyncClient) -> None:
    """GET /health/detailed is not a public route and requires auth."""
    response = await client.get("/health/detailed")
    assert response.status_code == 401
    assert response.json()["code"] == "MISSING_API_KEY"
