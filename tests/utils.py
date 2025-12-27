from httpx import AsyncClient, ASGITransport
from app.main import app

def get_client():
    return AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    )
