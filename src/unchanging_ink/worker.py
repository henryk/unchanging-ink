import asyncio
import base64
import datetime
import logging

import aioredis
import orjson
import sentry_sdk
import sqlalchemy
from alembic import command, config
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.sql.expression import bindparam, text

from unchanging_ink.cache import MainMerkleTree
from unchanging_ink.schemas import (IntervalProofStructure, IntervalTreeHead,
                                    MerkleTreeHead)

from .crypto import AbstractAsyncMerkleTree, DictCachingMerkleTree
from .models import interval, timestamp
from .server import engine

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
) -> MerkleTreeHead:
    now_ = datetime.datetime.now(datetime.timezone.utc)
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
                timestamp=now_.isoformat(timespec="microseconds").replace(
                    "+00:00", "Z"
                ),
                itmh=interval_tree_head.itmh,
            )
        )
        await conn.execute(text("SET CONSTRAINTS ALL DEFERRED"))

        redis = await aioredis.from_url("redis://redis/0")
        try:
            tree = MainMerkleTree(redis, conn)
            tree_root = await tree.calculate_node(0, interval_tree_head.interval+1)
        finally:
            if redis:
                await redis.close()

        mth_b64 = base64.b64encode(tree_root.value).decode()

        proofs = []
        for i, row in enumerate(rows):
            proofs.append(
                await formulate_proof(
                    interval_tree,
                    interval_tree_head,
                    i,
                    row,
                    f"dev.unchanging.ink/{interval_tree_head.interval}#v1:{mth_b64}",
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

        retval = MerkleTreeHead(interval=interval_tree_head.interval, mth=tree_root.value)
    return retval


def run_upgrade(connection, cfg):
    cfg.attributes["connection"] = connection
    command.upgrade(cfg, "head")


async def async_main():
    r_conn = await aioredis.from_url("redis://redis/0")

    logger.info("Upgrading database")
    async with engine.connect() as conn:
        await conn.run_sync(run_upgrade, config.Config("alembic.ini"))
        await conn.commit()

    logger.info("Worker ready")
    queue = []
    try:
        while True:
            await asyncio.sleep(3)
            async with engine.connect() as conn:
                mth = await calculate_interval(conn)
                await r_conn.publish("mth-live", mth.to_json())
                queue.append(orjson.loads(mth.to_json()))
                if len(queue) > 5:
                    queue.pop(0)
                await r_conn.set("recent-mth", orjson.dumps(queue))
    finally:
        await engine.dispose()


def main():
    logging.basicConfig(level=logging.DEBUG)
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
