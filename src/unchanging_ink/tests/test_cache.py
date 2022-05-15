from typing import Callable, Awaitable

import pytest

from unchanging_ink.cache import DictMerkleNodeCache
from unchanging_ink.crypto import MerkleTree


@pytest.fixture
def call_list():
    return []


@pytest.fixture
def standard_nodes(call_list) -> Callable[[int], Awaitable[bytes]]:
    async def s(x: int) -> bytes:
        call_list.append(x)
        return str(x).encode()
    return s


@pytest.mark.parametrize("number", list(range(1, 17)))
async def test_cache_size_sweep(number, call_list: list, standard_nodes):
    cache = DictMerkleNodeCache()
    compare_to = MerkleTree.from_sequence([await standard_nodes(x) for x in range(number)]).root.value
    call_list.clear()
    assert await cache.get_node(0, number, standard_nodes) == compare_to
    assert len(call_list) == number


async def test_cache_no_repeated_leafs(call_list: list, standard_nodes):
    cache = DictMerkleNodeCache()
    await cache.get_node(0, 17, standard_nodes)
    count_a = len(call_list)
    await cache.get_node(16, 18, standard_nodes)
    count_b = len(call_list)
    assert count_b - count_a == 1
    await cache.get_node(0, 8, standard_nodes)
    count_c = len(call_list)
    assert count_c == count_b


async def test_cache_retrieve(call_list: list, standard_nodes):
    cache = DictMerkleNodeCache()
    cache.seed({b"0,8": b"a"})
    await cache.get_node(0, 17, standard_nodes)
    assert len(call_list) == 17-8
