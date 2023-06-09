import asyncio
import base64
import datetime
import logging
import time
from typing import Optional, Tuple, TypeVar

import aioredis
import orjson
import sentry_sdk
import sqlalchemy
import structlog
from aioredis import Redis
from alembic import command, config
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.sql.expression import bindparam, text

from unchanging_ink.cache import MainMerkleTree
from unchanging_ink.schemas import (CompactRepr, ConcreteTime, Interval,
                                    IntervalProofStructure, MainHead,
                                    MainTreeConsistencyProof, MainHeadWithConsistency, MainTreeInclusionProof)

from .crypto import AbstractAsyncMerkleTree, DictCachingMerkleTree
from .models import interval as interval_model
from .models import timestamp
from .server import authority_base_url, engine, redis_url

logger = structlog.getLogger(__name__)


sentry_sdk.init(
    "https://67428a387e6f4703afd14b4b7fe92936@sentry.digitalwolff.de/10",
    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for performance monitoring.
    # We recommend adjusting this value in production.
    traces_sample_rate=1.0,
)


async def formulate_proof(
    interval_tree: AbstractAsyncMerkleTree,
    interval: Interval,
    i: int,
    row: dict,
    mth: CompactRepr,
) -> dict:
    a, path = await interval_tree.compute_inclusion_proof(i)
    return {
        "id_": row["id"],
        "interval": interval.index,
        "proof": IntervalProofStructure(
            a=a,
            path=[node.value for node in path],
            mth=mth,
            ith=interval.ith,
        ).to_cbor(),
    }


async def calculate_interval(
    conn: sqlalchemy.ext.asyncio.AsyncConnection,
    redisconn: Redis,
) -> MainHeadWithConsistency:
    logger.info("Starting calculate_interval()")
    start_time = time.time()
    async with conn.begin() as transaction:
        now_ = (
            datetime.datetime.now(datetime.timezone.utc)
            .isoformat(timespec="microseconds")
            .replace("+00:00", "Z")
        )
        s = (
            timestamp.select(timestamp.c.interval.is_(None))
            .with_for_update()
            .order_by("timestamp", "hash")
        )
        result = await conn.execute(s)

        rows = list(result)
        logger.debug("Have %i new rows", len(rows), time=time.time()-start_time)

        interval_tree = await DictCachingMerkleTree.from_sequence(
            row["hash"] for row in rows
        )
        print("New head", interval_tree.root)

        max_id = (
            await conn.execute(
                sqlalchemy.select(
                    [
                        sqlalchemy.func.max(
                            interval_model.c.id, type_=sqlalchemy.types.String
                        ).label("maxid")
                    ]
                )
            )
        ).scalar()
        interval = Interval(
            index=0 if max_id is None else max_id + 1,
            timestamp=now_,
            ith=interval_tree.root.value,
        )

        await conn.execute(
            interval_model.insert().values(
                id=interval.index,
                timestamp=now_,
                ith=interval.ith,
            )
        )
        await conn.execute(text("SET CONSTRAINTS ALL DEFERRED"))
        logger.info("Interval inserted", interval=interval, time=time.time()-start_time)

        tree_start_time = time.time()
        tree = MainMerkleTree(redisconn, conn)
        tree_root = await tree.recalculate_root(interval.index + 1)
        logger.info("New tree root", new_root=tree_root, time=time.time()-start_time, delta=time.time()-tree_start_time)

        mth_b64url = base64.urlsafe_b64encode(tree_root.value).decode().rstrip("=")
        mth = f"{authority_base_url}/{interval.index}#v1:{mth_b64url}"

        proofs = []
        for i, row in enumerate(rows):
            proofs.append(
                await formulate_proof(
                    interval_tree,
                    interval,
                    i,
                    row,
                    mth,
                )
            )

        logger.info("Inserting %i proofs", len(proofs), time=time.time()-start_time)
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

        if interval.index < 2:
            append_proof = None
        else:
            proof_nodes = await tree.compute_consistency_proof(interval.index - 1)
            append_proof = MainTreeConsistencyProof(
                interval.index - 1,
                interval.index,
                nodes=[node.value for node in proof_nodes],
            )

        logger.info("Computing current inclusion proof", time=time.time()-start_time)
        incp_start_time = time.time()
        a, path = await tree.compute_inclusion_proof(interval.index)
        inclusion_proof = MainTreeInclusionProof(
            head=interval.index,
            leaf=None,
            a=a,
            nodes=[node.value for node in path],
        )

        retval = MainHeadWithConsistency(
            authority=authority_base_url,
            interval=interval,
            mth=tree_root.value,
            inclusion=inclusion_proof,
            consistency=append_proof,
        )
        logger.info("calculate_interval() done", retval=retval, time=time.time()-start_time, delta=time.time()-incp_start_time)
    return retval


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
            await asyncio.sleep(3)  # Time between intervals
            async with aioredis.from_url(redis_url) as redisconn:
                async with engine.connect() as conn:
                    mth = await calculate_interval(conn, redisconn)
                    await conn.commit()
                live_data = mth.as_json_data()
                await redisconn.publish("mth-live", orjson.dumps(live_data))
                queue.append(live_data)
                if len(queue) > 5:
                    queue.pop(0)
                await redisconn.set("recent-mth", orjson.dumps(queue))
    finally:
        await engine.dispose()


def main():
    structlog.configure(wrapper_class=structlog.make_filtering_bound_logger(logging.INFO))
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
