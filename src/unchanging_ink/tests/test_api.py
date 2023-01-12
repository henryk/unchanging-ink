import pytest
from sanic_testing import TestManager


@pytest.fixture
def app():
    from ..server import app

    TestManager(app)

    return app


@pytest.mark.asyncio
async def test_api_hello(app):
    request, response = await app.asgi_client.get("/hello")

    assert response.status == 200
    assert response.json == {"Hello": "World"}
