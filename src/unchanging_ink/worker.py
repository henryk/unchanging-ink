import datetime
import logging
import time

import sqlalchemy
from nacl.encoding import Base64Encoder
from sqlalchemy import create_engine
from sqlalchemy.sql.expression import bindparam, select

from .crypto import MerkleNode
from .models import interval, signed_timestamp
from .server import db

logger = logging.getLogger(__name__)


def formulate_proof(full_index, i, row, interval_id, interval_hash_b64):
    # FIXME Draw the rest of the owl
    return {
        "id": row["id"],
        "interval": interval_id,
        "proof": {"ith": interval_hash_b64},
    }


def calculate_interval(conn: sqlalchemy.engine.Connection):
    print(datetime.datetime.now().isoformat())
    with conn.begin() as transaction:
        s = signed_timestamp.select(
            signed_timestamp.c.interval.is_(None), for_update=True
        ).order_by("timestamp", "signature")
        result = conn.execute(s)

        rows = list(result)
        if len(rows) == 0:
            return

        merkle_node, full_index = MerkleNode.from_sequence(
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
            signed_timestamp.update()
            .where(signed_timestamp.c.id == bindparam("id"))
            .values(
                interval=bindparam("interval"),
                proof=bindparam("proof"),
            ),
            proofs,
        )


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

    logger.info("Worker ready")
    while True:
        time.sleep(1)
        with engine.connect() as conn:
            calculate_interval(conn)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    main()
