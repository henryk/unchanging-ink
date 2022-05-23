import aioredis
from sanic import Sanic
from sqlalchemy.ext.asyncio import create_async_engine

from .crypto import setup_crypto
from .fanout import Fanout, redis_fanout
from .routes import setup_routes

app = Sanic(__name__.replace(".", "-"))
app.config.REAL_IP_HEADER = "X-Real-IP"

if "DB_USER" not in app.config:
    app.config.update(
        {
            "DB_USER": "sanic",
            "DB_HOST": "db",
            "DB_PASSWORD": "toomanysecrets",
            "DB_NAME": "sanic",
        }
    )

if "AUTHORITY" not in app.config:
    app.config.update({
        "AUTHORITY": "dev.unchanging.ink"
    })

db_url = f"postgresql+asyncpg://{app.config.DB_USER}:{app.config.DB_PASSWORD}@{app.config.DB_HOST}/{app.config.DB_NAME}"
redis_url = "redis://redis/0"
engine = create_async_engine(db_url)
authority_base_url = f"{app.config.AUTHORITY}"


def setup_database():
    @app.listener("before_server_start")
    async def prepare_db(*args, **kwargs):
        app.ctx.engine = create_async_engine(db_url, pool_size=0, max_overflow=-1)

    @app.listener("after_server_stop")
    async def stop_db():
        await app.ctx.engine.dispose()


def setup_fanout(app):
    @app.listener("before_server_start")
    async def create_fanout(*args, **kwargs):
        app.ctx.fanout = Fanout()
        app.add_task(redis_fanout)


def setup_redis(app):
    @app.listener("before_server_start")
    async def open_redis(*args, **kwargs):
        app.ctx.redis = await aioredis.from_url(redis_url)

    @app.listener("after_server_stop")
    async def close_redis():
        await app.ctx.redis.close()


def setup():
    setup_database()
    setup_redis(app)
    setup_routes(app)
    setup_crypto(app)
    setup_fanout(app)


def init():
    setup()

    workers = app.config.get("WORKERS", "auto")
    if str(workers).lower() == "auto":
        import multiprocessing

        workers = max(multiprocessing.cpu_count() - 1, 1)
    else:
        workers = int(workers)

    app.run(
        host=app.config.get("BIND_HOST", "127.0.0.1"),
        port=app.config.get("BIND_PORT", 8000),
        debug=app.config.get("DEBUG", False),
        workers=workers,
    )
