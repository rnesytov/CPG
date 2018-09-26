import pytest
from pathlib import Path
from gateway.app import create_app
from tests.helpers import clear_db


@pytest.fixture
async def app():
    config_path = Path(__file__).parent / 'cpg_configuration_test.yml'
    app = await create_app(config_path=config_path)
    app.cleanup_ctx.append(clear_db)

    return app


@pytest.fixture(autouse=True)
async def client(app, aiohttp_client):
    return await aiohttp_client(app)


@pytest.fixture
async def client_w_token(app, aiohttp_client):
    return await aiohttp_client(app, headers={'CPG_API_KEY': app.config.api_key})
