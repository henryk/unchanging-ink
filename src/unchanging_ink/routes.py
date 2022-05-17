import datetime
import logging
import uuid
from typing import TypeVar, Type

from accept_types import get_best_match
from nacl.encoding import Base64Encoder
from orjson import dumps as json_dumps
from sanic import Sanic
from sanic.request import Request
from sanic.response import HTTPResponse
from sanic.response import json as json_response

from .models import timestamp
from .schemas import TimestampStructure, Timestamp, TimestampWithId, TimestampRequest

logger = logging.getLogger(__name__)

T = TypeVar('T')


def data_from_request(request: Request, clazz: Type[T]) -> T:
    if request.headers["content-type"] == "application/cbor":
        return clazz.from_cbor(request.body)
    else:
        return clazz.from_json(request.body)


def data_to_response(request, data, *args, **kwargs) -> HTTPResponse:
    return_types = ['application/json', 'application/cbor']
    return_types.sort(key=lambda x: (x != 'application/cbor', x))
    return_type = get_best_match(request.headers.get('accept', request.headers.get('content-type', '*')), return_types)

    if return_type == "application/cbor":
        kwargs['content_type'] = 'application/cbor'
        return HTTPResponse(data.to_cbor(), *args, **kwargs)
    elif return_type == "application/json":
        kwargs['content_type'] = 'application/json'
        return HTTPResponse(data.to_json(), *args, **kwargs)
    else:
        return HTTPResponse(status=406)


def setup_routes(app: Sanic):
    @app.route("/ts/", version=1, methods=["GET", "POST"])  # FIXME Throttling
    async def request_timestamp(request: Request) -> HTTPResponse:
        if request.method == "GET":  # FIXME Remove
            query = timestamp.select()

            # FIXME Augment with interval itmh and mth
            rows = await request.app.ctx.db.fetch_all(query)
            return json_response(
                [
                    TimestampWithId(**{
                        k: v for (k, v) in row.items()
                        if k not in ("tag", )
                    }).as_json_data()
                    for row in rows
                ]
            )

        elif request.method == "POST":
            timestamp_request = data_from_request(request, TimestampRequest)
            now = datetime.datetime.now(datetime.timezone.utc)
            data = timestamp_request.data
            options = timestamp_request.options  # FIXME Implement options

            hash_ = TimestampStructure(data=data, timestamp=now).calculate_hash()

            st_id = uuid.uuid4()

            data = {
                "id": st_id,
                "timestamp": now.isoformat(timespec="microseconds").replace("+00:00", "Z"),
                "hash": hash_,
            }

            await app.ctx.db.execute(query=timestamp.insert(), values=data)

            response = Timestamp(hash=hash_, timestamp=data["timestamp"])

            return data_to_response(request, response, headers={"location": app.url_for('request_timestamp_one', id_=data["id"])})

    @app.route("/ts/<id_:uuid>", version=1, methods=["GET"])  # FIXME Throttling
    async def request_timestamp_one(request: Request, id_: uuid.UUID) -> HTTPResponse:
        query = timestamp.select(timestamp.c.id == id_)
        row = await request.app.ctx.db.fetch_one(query)
        response = TimestampWithId(**{
                        k: v for (k, v) in row.items()
                        if k not in ("tag", )
                    })
        return data_to_response(request, response)

    @app.route("/hello")
    async def hello(request: Request) -> HTTPResponse:
        return json_response({"Hello": "World"})

    @app.websocket("/mth/live", version=1)
    async def mth_live(request, ws):
        while True:
            data = await request.app.ctx.fanout.wait()
            await ws.send(data)
