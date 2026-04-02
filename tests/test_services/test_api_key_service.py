import pytest

from app.services.api_key_service import ApiKeyService


@pytest.mark.asyncio
async def test_create_key_returns_valid_format(_patch_config: None) -> None:
    service = ApiKeyService()
    key, response = service.create_key("test", "user", "default")
    assert key.startswith("sk-")
    assert len(key) > 10
    assert response.name == "test"
    assert response.role == "user"
    assert response.tenant_id == "default"
    assert response.id is not None


@pytest.mark.asyncio
async def test_validate_key_succeeds_with_correct_key(_patch_config: None) -> None:
    service = ApiKeyService()
    key, created = service.create_key("test-validate", "user", "default")
    validated = service.validate_key(key)
    assert validated is not None
    assert validated.id == created.id
    assert validated.role == "user"


@pytest.mark.asyncio
async def test_validate_key_fails_with_wrong_key(_patch_config: None) -> None:
    service = ApiKeyService()
    validated = service.validate_key("sk-wrongkey12345wrongwrongwrong")
    assert validated is None


@pytest.mark.asyncio
async def test_revoke_key_invalidates_it(_patch_config: None) -> None:
    service = ApiKeyService()
    key, created = service.create_key("test-revoke", "user", "default")
    revoked = service.revoke_key(str(created.id), "default")
    assert revoked is True
    validated = service.validate_key(key)
    assert validated is None


@pytest.mark.asyncio
async def test_revoke_nonexistent_key_returns_false(_patch_config: None) -> None:
    service = ApiKeyService()
    result = service.revoke_key("00000000-0000-0000-0000-000000000000", "default")
    assert result is False
