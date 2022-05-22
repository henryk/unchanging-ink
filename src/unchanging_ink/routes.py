import base64
import datetime
import logging
import uuid
from typing import Type, TypeVar

import cbor2
from accept_types import get_best_match
from sanic import Sanic
from sanic.exceptions import PayloadTooLarge
from sanic.request import Request
from sanic.response import HTTPResponse, text
from sanic.response import json as json_response

from .cache import MainMerkleTree
from .models import timestamp
from .schemas import (MerkleTreeConsistencyProof, MerkleTreeHead,
                      TimestampRequest, TimestampStructure, TimestampWithId)
from .server import authority_base_url

logger = logging.getLogger(__name__)

T = TypeVar("T")


def data_from_request(request: Request, clazz: Type[T]) -> T:
    if request.headers["content-type"] == "application/cbor":
        return clazz.from_cbor(request.body)
    else:
        return clazz.from_json(request.body)


def data_to_response(
    request: Request, data, *args, immutable=False, **kwargs
) -> HTTPResponse:
    return_types = ["application/json", "application/cbor"]
    return_types.sort(key=lambda x: (x != "application/cbor", x))
    return_type = get_best_match(
        request.headers.get("accept", request.headers.get("content-type", "*")),
        return_types,
    )

    headers = kwargs.get("headers", {})
    kwargs["headers"] = headers

    if immutable and request.method.lower() in ["get", "head", "options"]:
        headers["Vary"] = ", ".join(
            [x.strip() for x in headers.get("Vary", "").split(",") if x.strip()]
            + [x for x in ["accept", "content-type"] if x in request.headers]
        )
        headers["Cache-Control"] = "public, max-age=31536000, immutable"

    if return_type == "application/cbor":
        kwargs["content_type"] = "application/cbor"
        return HTTPResponse(data.to_cbor(), *args, **kwargs)
    elif return_type == "application/json":
        kwargs["content_type"] = "application/json"
        return HTTPResponse(data.to_json(), *args, **kwargs)
    else:
        return HTTPResponse(status=406)


def compact_encoding(response: TimestampWithId):
    return (
        f"{authority_base_url}/{response.interval}#v1,{response.timestamp},"
        + base64.urlsafe_b64encode(cbor2.dumps([response.proof.a, response.proof.path]))
        .decode()
        .rstrip("=")
    )


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
                        TimestampWithId.from_dict(row._asdict()).as_json_data()
                        for row in rows
                    ]
                )

        elif request.method == "POST":
            tag = None
            wait = False
            compact = False
            for (k, v) in request.query_args:
                if k == "tag" and len(v) <= 36:
                    tag = v
                elif k == "wait":
                    wait = True
                elif k == "compact":
                    compact = True
                    wait = True

            if compact:
                data = request.body
            else:
                timestamp_request = data_from_request(request, TimestampRequest)
                data = timestamp_request.data

            if len(data) > 256:
                raise PayloadTooLarge()

            now = (
                datetime.datetime.now(datetime.timezone.utc)
                .isoformat(timespec="microseconds")
                .replace("+00:00", "Z")
            )

            hash_ = TimestampStructure(data=data, timestamp=now).calculate_hash()

            st_id = uuid.uuid4()

            data = {"id": st_id, "timestamp": now, "hash": hash_, "tag": tag}

            async with app.ctx.engine.begin() as conn:
                await conn.execute(timestamp.insert(), data)

            if wait:
                # FIXME Timeout
                await request.app.ctx.fanout.wait()
                async with app.ctx.engine.begin() as conn:
                    result = await conn.execute(
                        timestamp.select().where(timestamp.c.id == st_id)
                    )
                    row = result.first()
                    response = TimestampWithId.from_dict(row._asdict())

            else:
                response = TimestampWithId.from_dict(data)

            headers = {
                "location": app.ctx.prefixed_url_for(
                    "request_timestamp_one",
                    id_=response.id,
                )
            }

            if compact:
                return text(compact_encoding(response))
            else:
                return data_to_response(request, response, headers=headers)

    @app.route("/ts/<id_:uuid>", version=1, methods=["GET"])  # FIXME Throttling
    async def request_timestamp_one(request: Request, id_: uuid.UUID) -> HTTPResponse:
        compact = False
        for (k, v) in request.query_args:
            if k == "compact":
                compact = True

        query = timestamp.select(timestamp.c.id == id_)
        async with app.ctx.engine.begin() as conn:
            result = await conn.execute(query)
            row = result.first()

        response = TimestampWithId.from_dict(row._asdict())

        if compact:
            return text(compact_encoding(response))

        return data_to_response(
            request, response
        )

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
        async with app.ctx.engine.begin() as conn, app.ctx.redis.client() as redisconn:
            tree = MainMerkleTree(redisconn, conn)
            node = await tree.calculate_node(0, interval + 1)
        response = MerkleTreeHead(interval=interval, mth=node.value)
        return data_to_response(request, response, immutable=True)

    @app.route(
        "/mth/<new_interval:int>/from/<old_interval:int>", version=1, methods=["GET"]
    )
    async def request_mth_proof(request, new_interval, old_interval):
        async with app.ctx.engine.begin() as conn, app.ctx.redis.client() as redisconn:
            tree = MainMerkleTree(redisconn, conn, width=new_interval)
            proof = await tree.compute_consistency_proof(old_interval)
        response = MerkleTreeConsistencyProof(
            old_interval, new_interval, [node.value for node in proof]
        )
        return data_to_response(request, response, immutable=True)
