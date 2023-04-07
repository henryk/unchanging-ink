from abc import ABC
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

import structlog
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine

from unchanging_ink.crypto import AbstractAsyncCachingMerkleTree, MerkleNode
from unchanging_ink.models import interval
from unchanging_ink.schemas import Interval

MAX_CACHE_WIDTH = 128
logger = structlog.getLogger(__name__)


class AbstractRedisAsyncCachingMerkleTree(AbstractAsyncCachingMerkleTree, ABC):
    def __init__(self, aiorediconn, *args, **kwargs):
        self._aiorc = aiorediconn
        super().__init__(*args, **kwargs)

    async def seed(self, data: Dict[Tuple[int, int], MerkleNode]):
        for k, v in data.items():
            await self._setc(k, v)

    async def _getc(self, key: Tuple[int, int]) -> Optional[MerkleNode]:
        bkey = "{},{}".format(*key).encode()
        value = await self._aiorc.get(bkey)
        logger.debug("_getc", key=key, value=value)
        if value is None:
            return None
        return MerkleNode(key[0], key[1], value)

    async def _setc(self, key: Tuple[int, int], value: MerkleNode):
        logger.debug("_setc", key=key, value=value)
        key = "{},{}".format(*key).encode()
        a = await self._aiorc.set(key, value.value, ex=60 * 60 * 24)
        logger.debug("set response", a=a)


@dataclass
class PreloadCache:
    start: int
    end: int
    data: dict


class MainMerkleTree(AbstractRedisAsyncCachingMerkleTree):
    def __init__(self, aioredisconn, conn: AsyncConnection, *args, **kwargs):
        self._conn = conn
        self._preload_cache: Optional[PreloadCache] = None
        super().__init__(aioredisconn, *args, **kwargs)

    async def _setc(self, key: Tuple[int, int], value: MerkleNode):
        if key[1] - key[0] <= MAX_CACHE_WIDTH:
            logger.debug("_setc noop", key=key)
            return
        return await super()._setc(key, value)

    async def _getc(self, key: Tuple[int, int]) -> Optional[MerkleNode]:
        # If preload_cache is set and keys fall within it, do not hit the redis cache,
        # instead don't return intermediate cached nodes, and let fetch_leaf data return
        # the cached data.
        # If preload cache is set and key falls outside, delete preload cache
        # If preload cache is not set, node is not cached, and end-start is within
        # cache_size, fetch and fill preload cache

        if self._preload_cache:
            if self._preload_cache.start <= key[0] < key[1] <= self._preload_cache.end:
                logger.debug("preload cache hit", start=self._preload_cache.start, end=self._preload_cache.end)
                return None
            else:
                logger.debug("preload cache cleared1")
                self._preload_cache = None

        retval = await super()._getc(key)

        if retval is None:
            if key[1] - key[0] <= MAX_CACHE_WIDTH:
                query = interval.select().where(
                    interval.c.id >= key[0], interval.c.id < key[1]
                )

                result = await self._conn.execute(query)
                rows = result.all()

                self._preload_cache = PreloadCache(
                    start=key[0], end=key[1], data={row.id: row for row in rows}
                )
                logger.debug("preload cache set", start=key[0], end=key[1])

        return retval

    async def fetch_leaf_data(self, position: int) -> bytes:
        row = None
        if self._preload_cache:
            if self._preload_cache.start <= position < self._preload_cache.end:
                row = self._preload_cache.data[position]
                logger.debug("preload cache used", position=position)
            else:
                self._preload_cache = None
                logger.debug("preload cache cleared2")

        if row is None:
            query = interval.select().where(interval.c.id == position)

            result = await self._conn.execute(query)
            row = result.first()

        ith = Interval.from_row(row)
        return ith.calculate_hash()
