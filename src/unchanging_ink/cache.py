import abc
from typing import Optional, Callable, Dict, Awaitable

from unchanging_ink.crypto import MerkleNode


class MerkleNodeCache:
    def __init__(self, get_item: Callable[[int], Awaitable[bytes]]):
        self.get_item = get_item

    @abc.abstractmethod
    async def _getc(self, key: bytes) -> Optional[bytes]:
        raise NotImplemented

    @abc.abstractmethod
    async def _setc(self, key: bytes, value: bytes):
        raise NotImplemented

    def seed(self, data: Dict[bytes, bytes]):
        raise NotImplemented

    async def get_node(self, start: int, end: int) -> bytes:
        key = "{},{}".format(start, end).encode()
        if (retval := await self._getc(key)) is not None:
            return retval

        assert start < end

        if start + 1 == end:
            item = MerkleNode.from_leaf(start, await self.get_item(start))
        else:
            mask_length = (start ^ (end - 1)).bit_length()
            middle = start + (1 << (mask_length - 1))

            left = MerkleNode(start, middle, await self.get_node(start, middle))
            right = MerkleNode(middle, end, await self.get_node(middle, end))
            item = MerkleNode.combine(left, right)

        await self._setc(key, item.value)
        return item.value

    async def get_path_proof(self, position, width) -> list[bytes]:
        pass

    async def get_inclusion_proof(self, old_width, new_width) -> list[bytes]:
        pass


class DictMerkleNodeCache(MerkleNodeCache):
    def __init__(self, get_item: Callable[[int], Awaitable[bytes]]):
        super().__init__(get_item)
        self._d = dict()

    def seed(self, data: Dict[bytes, bytes]):
        self._d.update(data)

    async def _getc(self, key: bytes) -> Optional[bytes]:
        return self._d.get(key, None)

    async def _setc(self, key: bytes, value: bytes):
        self._d[key] = value
