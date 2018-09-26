from aiohttp import web
from motor.motor_asyncio import AsyncIOMotorClient

from gateway.routes import setup_routes
from gateway.views import ApiHandler
from gateway.config import Configuration
from gateway.repositories import setup_repositories
from gateway.scheduler import setup_scheduler
from gateway.services import ManageIndexes


async def mongo_engine(app):
    mongo_conf = app.config.mongo

    mongo_uri = f"mongodb://{mongo_conf.host}:{mongo_conf.port}"
    db_name = mongo_conf.database

    conn = AsyncIOMotorClient(
        mongo_uri,
        username=mongo_conf.user,
        password=mongo_conf.password,
        authSource=mongo_conf.auth_source,
        maxPoolSize=mongo_conf.max_pool_size,
        io_loop=app.loop,
        connect=True,
        connectTimeoutMS=5000)

    app.mongo = conn[db_name]

    await ManageIndexes(app)()

    yield

    conn.close()


async def create_app(config_path=''):
    config = Configuration.load(config_path)
    config.setup_logging()

    app = web.Application()
    app.config = config

    app.cleanup_ctx.append(mongo_engine)
    app.cleanup_ctx.append(setup_repositories)
    app.cleanup_ctx.append(setup_scheduler)

    handler = ApiHandler(app)
    setup_routes(app, handler)

    return app
