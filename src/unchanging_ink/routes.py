import datetime
import logging
import uuid
from typing import Type, TypeVar

from accept_types import get_best_match
from sanic import Sanic
from sanic.request import Request
from sanic.response import HTTPResponse
from sanic.response import json as json_response

from .cache import MainMerkleTree
from .models import timestamp
from .schemas import (MerkleTreeHead, Timestamp, TimestampRequest,
                      TimestampStructure, TimestampWithId)

logger = logging.getLogger(__name__)

T = TypeVar("T")


def data_from_request(request: Request, clazz: Type[T]) -> T:
    if request.headers["content-type"] == "application/cbor":
        return clazz.from_cbor(request.body)
    else:
        return clazz.from_json(request.body)


def data_to_response(request: Request, data, *args, immutable=False, **kwargs) -> HTTPResponse:
    return_types = ["application/json", "application/cbor"]
    return_types.sort(key=lambda x: (x != "application/cbor", x))
    return_type = get_best_match(
        request.headers.get("accept", request.headers.get("content-type", "*")),
        return_types,
    )

    headers = kwargs.get("headers", {})
    kwargs['headers'] = headers

    if immutable and request.method.lower() in ['get', 'head', 'options']:
        headers['Vary'] = ", ".join([x.strip() for x in headers.get('Vary', '').split(",") if x.strip()]+[
            x for x in ['accept', 'content-type'] if x in request.headers
        ])
        headers['Cache-Control'] = 'public, max-age=31536000, immutable'

    if return_type == "application/cbor":
        kwargs["content_type"] = "application/cbor"
        return HTTPResponse(data.to_cbor(), *args, **kwargs)
    elif return_type == "application/json":
        kwargs["content_type"] = "application/json"
        return HTTPResponse(data.to_json(), *args, **kwargs)
    else:
        return HTTPResponse(status=406)


def setup_routes(app: Sanic):
    def prefixed_url_for(*args, **kwargs):
        # FIXME make work for _external=True
        route = app.url_for(*args, **kwargs)
        return "/api" + route

    app.ctx.prefixed_url_for = prefixed_url_for

    @app.route("/ts/", version=1, methods=["GET", "POST"])  # FIXME Throttling
    async def request_timestamp(request: Request) -> HTTPResponse:
        if request.method == "GET":  # FIXME Remove
            query = timestamp.select()

            async with app.ctx.engine.begin() as conn:
                result = await conn.execute(query)
                rows = result.all()
                return json_response(
                    [
                        TimestampWithId(
                            **{
                                k: v
                                for (k, v) in row._asdict().items()
                                if k not in ("tag",)
                            }
                        ).as_json_data()
                        for row in rows
                    ]
                )

        elif request.method == "POST":
            timestamp_request = data_from_request(request, TimestampRequest)
            now = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="microseconds").replace(
                    "+00:00", "Z"
                )
            data = timestamp_request.data
            options = timestamp_request.options  # FIXME Implement options

            hash_ = TimestampStructure(data=data, timestamp=now).calculate_hash()

            st_id = uuid.uuid4()

            data = {
                "id": st_id,
                "timestamp": now,
                "hash": hash_,
            }

            async with app.ctx.engine.begin() as conn:
                await conn.execute(timestamp.insert(), data)

            response = Timestamp(hash=hash_, timestamp=now)

            return data_to_response(
                request,
                response,
                headers={
                    "location": app.ctx.prefixed_url_for(
                        "request_timestamp_one", id_=data["id"]
                    )
                },
            )

    @app.route("/ts/<id_:uuid>", version=1, methods=["GET"])  # FIXME Throttling
    async def request_timestamp_one(request: Request, id_: uuid.UUID) -> HTTPResponse:
        query = timestamp.select(timestamp.c.id == id_)
        async with app.ctx.engine.begin() as conn:
            result = await conn.execute(query)
            row = result.first()

        response = TimestampWithId(
            **{k: v for (k, v) in row._asdict().items() if k not in ("tag",)}
        )
        return data_to_response(request, response)

    @app.route("/hello")
    async def hello(request: Request) -> HTTPResponse:
        return json_response({"Hello": "World"})

    @app.websocket("/mth/live", version=1)
    async def mth_live(request, ws):
        while True:
            data = await request.app.ctx.fanout.wait()
            await ws.send(data)

    @app.route("/mth/<interval:int>", version=1, methods=["GET"])
    async def request_mth_one(request, interval):
        async with app.ctx.engine.begin() as conn:
            async with app.ctx.redis.client() as redisconn:
                tree = MainMerkleTree(redisconn, conn)
                node = await tree.calculate_node(0, interval+1)
        response = MerkleTreeHead(interval=interval, mth=node.value)
        return data_to_response(request, response, immutable=True)
