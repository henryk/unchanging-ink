import datetime
import logging
import uuid

from nacl.encoding import Base64Encoder
from orjson import dumps as json_dumps
from sanic import Sanic
from sanic.request import Request
from sanic.response import HTTPResponse
from sanic.response import json as json_response

from .models import timestamp

logger = logging.getLogger(__name__)


def setup_routes(app: Sanic):
    @app.route("/ts/", version=1, methods=["GET", "POST"])  # FIXME Throttling
    async def request_timestamp(request: Request) -> HTTPResponse:
        if request.method == "GET":  # FIXME Remove
            query = timestamp.select()

            rows = await request.app.ctx.db.fetch_all(query)
            return json_response(
                [
                    {
                        "id": str(row["id"]),
                        "hash": Base64Encoder.encode(row["hash"]).decode("us-ascii"),
                        "timestamp": row["timestamp"],
                        "version": "1",
                        "typ": "st",
                        "interval": row["interval"],
                        "proof": row["proof"],
                    }
                    for row in rows
                ]
            )

        elif request.method == "POST":
            now = datetime.datetime.now(datetime.timezone.utc)
            data = request.json["data"]
            options = request.json.get("options", [])
            timestamp_ = now.isoformat(timespec="microseconds").replace("+00:00", "Z")
            kid = app.ctx.crypto.kid

            signed_statement = (
                b'{"data":%s,"kid":%s,"timestamp":"%s","typ":"st","version":"1"}'
                % (
                    json_dumps(data),
                    json_dumps(kid),
                    timestamp.encode("us-ascii"),
                )
            )

            hash = app.ctx.crypto.sign(signed_statement)
            st_id = uuid.uuid4()

            data = {
                "id": st_id,
                "timestamp": timestamp,
                "hash": hash,
            }

            await app.ctx.db.execute(query=timestamp.insert(), values=data)

            data.update(
                {
                    "version": "1",
                    "typ": "st",
                    "id": str(st_id),
                    "hash": Base64Encoder.encode(hash).decode("us-ascii"),
                }
            )

            return json_response(data)

    @app.route("/ts/<id_:uuid>", version=1, methods=["GET"])  # FIXME Throttling
    async def request_timestamp_one(request: Request, id_: uuid.UUID) -> HTTPResponse:
        query = timestamp.query(timestamp.c.id == id_)
        row = await request.app.ctx.db.fetch_one(query)
        return json_response(
            {
                "id": str(row["id"]),
                "hash": Base64Encoder.encode(row["hash"]).decode("us-ascii"),
                "timestamp": row["timestamp"],
                "version": "1",
                "typ": "st",
                "interval": row["interval"],
                "proof": row["proof"],
            }
        )

    @app.route("/hello")
    async def hello(request: Request) -> HTTPResponse:
        return json_response({"Hello": "World"})

    @app.websocket("/mth/live", version=1)
    async def mth_live(request, ws):
        while True:
            data = await request.app.ctx.fanout.wait()
            await ws.send(data)
