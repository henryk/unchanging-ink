import datetime
import logging
import random
import time
from typing import Dict, Tuple

import orjson
import redis
import sentry_sdk
import sqlalchemy
from nacl.encoding import Base64Encoder
from sqlalchemy import create_engine
from sqlalchemy.sql.expression import bindparam

from .crypto import MerkleNode
from .models import interval, timestamp
from .server import db

logger = logging.getLogger(__name__)


sentry_sdk.init(
    "https://67428a387e6f4703afd14b4b7fe92936@sentry.digitalwolff.de/10",
    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for performance monitoring.
    # We recommend adjusting this value in production.
    traces_sample_rate=1.0,
)


def formulate_proof(
    full_index: Dict[Tuple[int, int], MerkleNode],
    i: int,
    row,
    interval_id,
    interval_hash_b64,
):
    # FIXME Draw the rest of the owl
    return {
        "id_": row["id"],
        "interval": interval_id,
        "proof": {"ith": interval_hash_b64},
    }


def calculate_interval(conn: sqlalchemy.engine.Connection) -> dict:
    retval = {
        "timestamp": datetime.datetime.now().isoformat(),
        "hash": "".join(random.choice("ABCDEF0123456789") for _ in range(64)),
    }
    with conn.begin() as transaction:
        s = (
            timestamp.select(timestamp.c.interval.is_(None))
            .with_for_update()
            .order_by("timestamp", "hash")
        )
        result = conn.execute(s)

        rows = list(result)
        if len(rows) == 0:
            return retval

        merkle_node, full_index = MerkleNode.from_sequence_with_index(
            row["signature"] for row in rows
        )
        print("New head", merkle_node)

        ith_obj = {"ith": merkle_node.value}
        max_id = conn.execute(
            sqlalchemy.select(
                [
                    sqlalchemy.func.max(
                        interval.c.id, type_=sqlalchemy.types.String
                    ).label("maxid")
                ]
            )
        ).scalar()
        ith_obj["id"] = 0 if max_id is None else max_id + 1
        ith_b64 = Base64Encoder.encode(merkle_node.value).decode("us-ascii")

        proofs = []
        for i, row in enumerate(rows):
            proofs.append(formulate_proof(full_index, i, row, ith_obj["id"], ith_b64))

        conn.execute(interval.insert().values(**ith_obj))
        conn.execute("SET CONSTRAINTS ALL DEFERRED")

        conn.execute(
            timestamp.update()
            .where(timestamp.c.id == bindparam("id_"))
            .values(
                interval=bindparam("interval"),
                proof=bindparam("proof"),
            ),
            proofs,
        )
    return retval


def main():
    logger.info("Upgrading database")
    import alembic.config

    alembicArgs = [
        "--raiseerr",
        "upgrade",
        "head",
    ]
    alembic.config.main(argv=alembicArgs)

    engine = create_engine(str(db.url))
    r_conn = redis.Redis(host="redis", port=6379, db=0)

    logger.info("Worker ready")
    queue = []
    while True:
        time.sleep(3)
        with engine.connect() as conn:
            mth = calculate_interval(conn)
            r_conn.publish("mth-live", orjson.dumps(mth))
            queue.append(mth)
            if len(queue) > 5:
                queue.pop(0)
            r_conn.set("recent-mth", orjson.dumps(queue))


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    main()
