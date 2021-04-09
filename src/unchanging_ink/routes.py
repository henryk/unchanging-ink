from sanic.request import Request
from sanic.response import HTTPResponse, json

from .models import signed_timestamp


def setup_routes(app):
    @app.route("/st")
    async def book_list(request: Request) -> HTTPResponse:
        query = signed_timestamp.select()
        rows = await request.app.ctx.db.fetch_all(query)
        return json(
            [
                {"signature": row["signature"], "timestamp": row["timestamp"]}
                for row in rows
            ]
        )

    @app.route("/hello")
    async def hello(request: Request) -> HTTPResponse:
        return json({"Hello": "World"})
