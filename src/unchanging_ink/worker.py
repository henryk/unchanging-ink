from nacl.encoding import Base64Encoder
import datetime
import time
import logging

import sqlalchemy
from sqlalchemy import create_engine

from .crypto import MerkleNode
from .models import signed_timestamp, interval
from .server import db

logger = logging.getLogger(__name__)


def formulate_proof(full_index, i, row):
    # FIXME Draw the rest of the owl
    return {"id": row["id"]}


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
        ith_b64 = Base64Encoder.encode(merkle_node.value).decode("us-ascii")
        proofs = []
        for i, row in enumerate(rows):
            proofs.append(formulate_proof(full_index, i, row))

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
        conn.execute(interval.insert().values(**ith_obj))

        for proof in proofs:
            id_ = proof.pop("id")
            proof["ith"] = ith_b64
            conn.execute(
                signed_timestamp.update()
                .where(signed_timestamp.c.id == id_)
                .values(interval=ith_obj["id"], proof=proof)
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
