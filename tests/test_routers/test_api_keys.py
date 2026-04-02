import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_key_returns_plaintext(
    client: AsyncClient, admin_key_header: dict[str, str]
) -> None:
    response = await client.post(
        "/v1/keys",
        json={"name": "test-key", "role": "user"},
        headers=admin_key_header,
    )
    assert response.status_code == 201
    body = response.json()
    assert body["key"].startswith("sk-")
    assert "id" in body
    assert body["role"] == "user"
    assert body["name"] == "test-key"


@pytest.mark.asyncio
async def test_create_key_requires_admin(
    client: AsyncClient, user_key_header: dict[str, str]
) -> None:
    response = await client.post(
        "/v1/keys",
        json={"name": "should-fail"},
        headers=user_key_header,
    )
    assert response.status_code == 403
    assert response.json()["code"] == "INSUFFICIENT_PERMISSIONS"


@pytest.mark.asyncio
async def test_missing_auth_returns_401(client: AsyncClient) -> None:
    response = await client.post("/v1/keys", json={"name": "test"})
    assert response.status_code == 401
    assert response.json()["code"] == "MISSING_API_KEY"


@pytest.mark.asyncio
async def test_revoke_key(
    client: AsyncClient, admin_key_header: dict[str, str]
) -> None:
    # Create a key
    create_resp = await client.post(
        "/v1/keys",
        json={"name": "to-revoke"},
        headers=admin_key_header,
    )
    assert create_resp.status_code == 201
    key_id = create_resp.json()["id"]
    plaintext = create_resp.json()["key"]

    # Revoke it
    revoke_resp = await client.delete(f"/v1/keys/{key_id}", headers=admin_key_header)
    assert revoke_resp.status_code == 204

    # The revoked key should now return 401
    verify_resp = await client.get(
        "/health/detailed",
        headers={"Authorization": f"Bearer {plaintext}"},
    )
    assert verify_resp.status_code == 401


@pytest.mark.asyncio
async def test_list_keys(
    client: AsyncClient, admin_key_header: dict[str, str]
) -> None:
    response = await client.get("/v1/keys", headers=admin_key_header)
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list)
    # At minimum the admin key used to make this request should be listed
    assert len(body) >= 1
    assert all("id" in k and "name" in k and "role" in k for k in body)
