import asyncio
import base64
import datetime
import logging
from typing import Optional, Tuple

import aioredis
import orjson
import sentry_sdk
import sqlalchemy
from aioredis import Redis
from alembic import command, config
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.sql.expression import bindparam, text

from unchanging_ink.cache import MainMerkleTree
from unchanging_ink.schemas import (IntervalProofStructure, IntervalTreeHead,
                                    MerkleTreeConsistencyProof, MerkleTreeHead)

from .crypto import AbstractAsyncMerkleTree, DictCachingMerkleTree
from .models import interval, timestamp
from .server import engine, redis_url, authority_base_url

logger = logging.getLogger(__name__)


sentry_sdk.init(
    "https://67428a387e6f4703afd14b4b7fe92936@sentry.digitalwolff.de/10",
    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for performance monitoring.
    # We recommend adjusting this value in production.
    traces_sample_rate=1.0,
)


async def formulate_proof(
    interval_tree: AbstractAsyncMerkleTree,
    interval_tree_head: IntervalTreeHead,
    i: int,
    row: dict,
    mth: str,
) -> dict:
    a, path = await interval_tree.compute_inclusion_proof(i)
    return {
        "id_": row["id"],
        "interval": interval_tree_head.interval,
        "proof": IntervalProofStructure(
            a=a,
            path=[node.value for node in path],
            mth=mth,
            itmh=interval_tree_head.itmh,
        ).to_cbor(),
    }


async def calculate_interval(
    conn: sqlalchemy.ext.asyncio.AsyncConnection,
    redisconn: Redis,
) -> Tuple[str, MerkleTreeHead, Optional[MerkleTreeConsistencyProof]]:
    now_ = (
        datetime.datetime.now(datetime.timezone.utc)
        .isoformat(timespec="microseconds")
        .replace("+00:00", "Z")
    )
    async with conn.begin() as transaction:
        s = (
            timestamp.select(timestamp.c.interval.is_(None))
            .with_for_update()
            .order_by("timestamp", "hash")
        )
        result = await conn.execute(s)

        rows = list(result)

        interval_tree = await DictCachingMerkleTree.from_sequence(
            row["hash"] for row in rows
        )
        print("New head", interval_tree.root)

        max_id = (
            await conn.execute(
                sqlalchemy.select(
                    [
                        sqlalchemy.func.max(
                            interval.c.id, type_=sqlalchemy.types.String
                        ).label("maxid")
                    ]
                )
            )
        ).scalar()
        interval_tree_head = IntervalTreeHead(
            interval=0 if max_id is None else max_id + 1,
            timestamp=now_,
            itmh=interval_tree.root.value,
        )

        await conn.execute(
            interval.insert().values(
                id=interval_tree_head.interval,
                timestamp=now_,
                itmh=interval_tree_head.itmh,
            )
        )
        await conn.execute(text("SET CONSTRAINTS ALL DEFERRED"))

        tree = MainMerkleTree(redisconn, conn)
        tree_root = await tree.recalculate_root(interval_tree_head.interval + 1)

        mth_b64url = base64.urlsafe_b64encode(tree_root.value).decode().rstrip("=")

        proofs = []
        for i, row in enumerate(rows):
            proofs.append(
                await formulate_proof(
                    interval_tree,
                    interval_tree_head,
                    i,
                    row,
                    f"{authority_base_url}/{interval_tree_head.interval}#v1:{mth_b64url}",
                )
            )

        if proofs:
            await conn.execute(
                timestamp.update()
                .where(timestamp.c.id == bindparam("id_"))
                .values(
                    interval=bindparam("interval"),
                    proof=bindparam("proof"),
                ),
                proofs,
            )

        if interval_tree_head.interval < 2:
            append_proof = None
        else:
            proof_nodes = await tree.compute_consistency_proof(
                interval_tree_head.interval - 1
            )
            append_proof = MerkleTreeConsistencyProof(
                interval_tree_head.interval - 1,
                interval_tree_head.interval,
                nodes=[node.value for node in proof_nodes],
            )

        retval = MerkleTreeHead(
            interval=interval_tree_head.interval, mth=tree_root.value
        )
    return now_, retval, append_proof


def run_upgrade(connection, cfg):
    cfg.attributes["connection"] = connection
    command.upgrade(cfg, "head")


async def async_main():
    logger.info("Upgrading database")
    async with engine.connect() as conn:
        await conn.run_sync(run_upgrade, config.Config("alembic.ini"))
        await conn.commit()

    logger.info("Worker ready")
    queue = []
    try:
        while True:
            await asyncio.sleep(3)
            async with aioredis.from_url(redis_url) as redisconn:
                async with engine.connect() as conn:
                    now_, mth, append_proof = await calculate_interval(conn, redisconn)
                    await conn.commit()
                live_data = mth.as_json_data()
                live_data["timestamp"] = now_
                live_data["proof"] = (
                    append_proof.as_json_data() if append_proof else None
                )
                await redisconn.publish("mth-live", orjson.dumps(live_data))
                queue.append(live_data)
                if len(queue) > 5:
                    queue.pop(0)
                await redisconn.set("recent-mth", orjson.dumps(queue))
    finally:
        await engine.dispose()


def main():
    logging.basicConfig(level=logging.DEBUG)
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
