import asyncio
import sys
from functools import wraps

import aioredis
import pytest

from unchanging_ink.cache import AbstractRedisAsyncCachingMerkleTree
from .test_merkle import StandardMerkleTreeUncached


if sys.platform == 'win32':
    # Work around https://github.com/kmike/port-for/issues/4
    import port_for.api as _a

    @wraps(_a._refuses_connection)
    def foo(*args, **kwargs):
        return True
    _a._refuses_connection = foo
    del _a, foo


if sys.platform.startswith("win"):
    pytest.skip("skipping redis tests on windows", allow_module_level=True)


class StandardMerkleTreeRedisCached(AbstractRedisAsyncCachingMerkleTree):
    def __init__(self, *args, **kwargs):
        self.nodes_generated = 0
        super().__init__(*args, **kwargs)

    async def fetch_leaf_data(self, position: int) -> bytes:
        self.nodes_generated += 1
        return str(position).encode()


@pytest.fixture
async def aioredisconn(redis_proc):
    redis = None
    try:
        redis = aioredis.from_url(f"redis://{redis_proc.host}:{redis_proc.port}")
        yield redis
    finally:
        if redis:
            await redis.flushdb()
            await redis.close()
            await redis.connection_pool.disconnect(inuse_connections=False)


async def test_redis_sanity_check(aioredisconn):
    await aioredisconn.set(b"0", b"0")
    assert (await aioredisconn.get("0")) == b"0"


async def test_redis_merkle_1(aioredisconn):
    tree = StandardMerkleTreeRedisCached(aioredisconn, width=7)
    await tree.calculate_node(0, tree.width)
    assert tree.nodes_generated == tree.width
    await tree.calculate_node(0, tree.width // 2)
    assert tree.nodes_generated == tree.width


async def test_redis_merkle_2(aioredisconn):
    tree_a = StandardMerkleTreeUncached(width=23)
    tree_b = StandardMerkleTreeRedisCached(aioredisconn, width=23)

    assert (await tree_a.calculate_node(0, 23)) == (await tree_b.calculate_node(0, 23))
