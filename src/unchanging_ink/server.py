from databases import Database
from sanic import Sanic

from .crypto import setup_crypto
from .routes import setup_routes

app = Sanic(__name__)
db = Database(
    f"postgresql://{app.config.DB_USER}:{app.config.DB_PASSWORD}@{app.config.DB_HOST}/{app.config.DB_NAME}"
)


def setup_database():
    app.ctx.db = db

    @app.listener("after_server_start")
    async def connect_to_db(*args, **kwargs):
        await app.ctx.db.connect()

    @app.listener("after_server_stop")
    async def disconnect_from_db(*args, **kwargs):
        await app.ctx.db.disconnect()


def init():
    setup_database()
    setup_routes(app)
    setup_crypto(app)

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
