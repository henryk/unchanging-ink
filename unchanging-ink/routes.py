from sanic.request import Request
from sanic.response import json, HTTPResponse


def setup_routes(app):
    @app.route("/ts")
    async def book_list(request: Request) -> HTTPResponse:
        #query = ts.select()
        #rows = await request.app.db.fetch_all(query)
        rows = []
        return json({
            'ts': [{row['title']: row['author']} for row in rows]
        })

    @app.route("/hello")
    async def hello(request: Request) -> HTTPResponse:
        return json({
            "Hello": "World"
        })
