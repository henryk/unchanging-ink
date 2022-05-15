from abc import ABC
from typing import Dict, Optional, Tuple

from unchanging_ink.crypto import AbstractAsyncCachingMerkleTree, MerkleNode


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
        if value is None:
            return None
        return MerkleNode(key[0], key[1], value)

    async def _setc(self, key: Tuple[int, int], value: MerkleNode):
        key = "{},{}".format(*key).encode()
        await self._aiorc.set(key, value.value)
