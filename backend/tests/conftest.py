# tests/conftest.py

import uuid
from unittest.mock import patch



import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport




from app.main import app
from app.core.database import engine
from app.core.redis_client import redis_client


class FakeLLM:
    async def generate(self, system_prompt: str, user_prompt: str) -> str:
        return "Test response."

    async def generate_with_tools(
        self,
        system_prompt: str,
        messages: list[dict],
        tools: list,
    ) -> dict:
        return {
            "type": "text",
            "content": "Test response.",
        }


@pytest.fixture(autouse=True)
def mock_llm_provider():
    fake_llm = FakeLLM()

    with patch(
        "app.copilot.router.get_llm_provider",
        return_value=fake_llm,
    ):
        yield

        

def pytest_collection_modifyitems(config, items):
    """Force every async test onto the SAME session-scoped event loop as
    the session-scoped async fixtures below, so the global SQLAlchemy
    engine / asyncpg pool and Redis client are never used from more than
    one loop. pytest-asyncio 0.24 has no ini-level option for this —
    loop_scope must be set per test, so we inject it here instead of
    touching every test function."""
    for item in items:
        if "asyncio" in item.keywords:
            item.add_marker(pytest.mark.asyncio(loop_scope="session"))


@pytest_asyncio.fixture(scope="session", autouse=True)
async def _dispose_shared_connections():
    yield
    await engine.dispose()
    await redis_client.aclose()


@pytest_asyncio.fixture(autouse=True)
async def _reset_rate_limits():
    """Test-only: clear rate-limit counters before each test. Production
    rate_limit.py is untouched."""
    async for key in redis_client.scan_iter("ratelimit:*"):
        await redis_client.delete(key)
    yield


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


async def register_and_login(client: AsyncClient) -> tuple[str, dict]:
    email = f"test-{uuid.uuid4().hex[:10]}@example.com"
    password = "testpass123"
    await client.post("/api/auth/register", json={
        "email": email, "password": password, "full_name": "Test User",
    })
    res = await client.post("/api/auth/login", json={"email": email, "password": password})
    token = res.json()["access_token"]
    return email, {"Authorization": f"Bearer {token}"}


async def grant_all_consents(client: AsyncClient, headers: dict):
    for purpose in ["financial_analysis", "fraud_analysis", "personalised_recommendations"]:
        await client.post("/api/consents", json={"purpose": purpose}, headers=headers)


@pytest_asyncio.fixture
async def user_a(client):
    email, headers = await register_and_login(client)
    await grant_all_consents(client, headers)
    return headers


@pytest_asyncio.fixture
async def user_b(client):
    email, headers = await register_and_login(client)
    await grant_all_consents(client, headers)
    return headers