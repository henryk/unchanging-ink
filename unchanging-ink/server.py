from sanic import Sanic
from environs import Env
from .routes import setup_routes
from databases import Database

app = Sanic(__name__)


def setup_database():
    app.ctx.db = Database("postgresql://postgres:postgres@localhost/postgres")

    @app.listener('after_server_start')
    async def connect_to_db(*args, **kwargs):
        await app.ctx.db.connect()

    @app.listener('after_server_stop')
    async def disconnect_from_db(*args, **kwargs):
        await app.ctx.db.disconnect()


def init():
    env = Env()
    env.read_env()

    #setup_database()
    setup_routes(app)

    app.run(
        host="127.0.0.1",
        port=8000,
        debug=True,
        auto_reload=True,
        workers=1,
    )
