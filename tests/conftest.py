import httpx
import pytest
import pytest_asyncio
from app import app, users_db, tasks_db

@pytest.fixture(autouse=True)
def clear_databases():
    """Очищает базы перед каждым тестом."""
    users_db.clear()
    tasks_db.clear()


@pytest_asyncio.fixture
async def client():
    """Создает асинхронный HTTPX клиент для тестирования FastAPI."""
    async with httpx.AsyncClient(
        base_url="http://test",
        transport=httpx.ASGITransport(app=app)
    ) as ac:
        yield ac