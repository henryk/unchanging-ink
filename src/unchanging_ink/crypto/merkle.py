from __future__ import annotations

import math
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from hashlib import sha512
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


@dataclass
class MerkleNode:
    start: int
    end: int
    value: bytes
    height: Optional[int] = field(init=False)
    hash_function = sha512

    def __post_init__(self):
        if self.end == self.start:
            self.height = 0
        else:
            self.height = int(math.ceil(math.log2(self.end - self.start))) + 1

    def __add__(self, other):
        assert isinstance(other, self.__class__)
        return self.combine(self, other)

    @classmethod
    def combine(cls: MerkleNode, n1: MerkleNode, n2: MerkleNode) -> MerkleNode:
        assert n1.end == n2.start
        return MerkleNode(
            n1.start, n2.end, cls.hash_function(b"\x01" + n1.value + n2.value).digest()
        )

    @classmethod
    def from_leaf(cls: MerkleNode, index: int, value: bytes) -> MerkleNode:
        return MerkleNode(index, index + 1, cls.hash_function(b"\x00" + value).digest())


class AbstractAsyncMerkleTree(ABC):
    NODE_CLASS = MerkleNode
    __slots__ = ("root", "width")

    def __init__(
        self, *, root: Optional[MerkleNode] = None, width: Optional[int] = None
    ):
        self.root: Optional[MerkleNode] = root
        self.width = self.root.end if self.root else width

    @abstractmethod
    async def fetch_leaf_data(self, position: int) -> bytes:
        raise NotImplementedError()

    @classmethod
    def consistency_proof_node_addresses(
        cls, old_width, new_width
    ) -> Iterable[Tuple[int, int]]:
        yield from cls._consistency_proof_subnode_addresses(old_width, new_width, True)

    @classmethod
    def _consistency_proof_subnode_addresses(
        cls, m: int, n: int, flag: bool, _o: int = 0
    ) -> Iterable[Tuple[int, int]]:
        assert 0 < m
        if n == m:
            if flag:
                return ()
            else:
                yield _o + 0, _o + n
        else:
            assert m < n
            k = 2 ** (math.ceil(math.log2(n)) - 1)
            if m <= k:
                yield from cls._consistency_proof_subnode_addresses(m, k, flag, _o)
                yield _o + k, _o + n
            else:
                yield from cls._consistency_proof_subnode_addresses(
                    m - k, n - k, False, _o + k
                )
                yield _o + 0, _o + k

    async def calculate_node(self, start: int, end: int) -> MerkleNode:
        assert start < end

        if start + 1 == end:
            item = MerkleNode.from_leaf(start, await self.fetch_leaf_data(start))
        else:
            mask_length = (start ^ (end - 1)).bit_length()
            middle = start + (1 << (mask_length - 1))

            item = await self.calculate_node(start, middle) + await self.calculate_node(
                middle, end
            )

        return item

    async def compute_inclusion_proof(
        self, position: int
    ) -> Tuple[int, Sequence[MerkleNode]]:
        current_read_bit: int = 1
        current_write_bit: int = 1
        current_width: int = 1
        path: int = 0
        neighbours: List[MerkleNode] = []

        mytree: MerkleNode = await self.calculate_node(position, position + 1)
        while not (mytree.start == 0 and mytree.end == self.width):
            if mytree.start & current_read_bit == 0:
                # This is the left side
                otherend = min(self.width, mytree.end + current_width)
                if mytree.end != otherend:
                    othertree = await self.calculate_node(mytree.end, otherend)
                else:
                    othertree = None
                # Do not OR in current_write_bit
            else:
                # Right side
                otherstart = max(0, mytree.start - current_width)
                if mytree.start != otherstart:
                    othertree = await self.calculate_node(otherstart, mytree.start)
                    path |= current_write_bit
                else:
                    othertree = None

            current_width *= 2
            current_read_bit <<= 1

            if othertree is None:
                # There is no other side
                continue

            if othertree.start == 0 and othertree.end == self.width:
                break

            current_write_bit <<= 1
            neighbours.append(othertree)

            mytree = await self.calculate_node(
                min(mytree.start, othertree.start), max(mytree.end, othertree.end)
            )

        return path, neighbours

    def verify_inclusion_proof(
        self,
        leaf_node: MerkleNode,
        path: int,
        neighbours: Sequence[MerkleNode],
    ) -> bool:
        current_node = leaf_node
        for neighbour in neighbours:
            if path & 1 == 0:
                # Left side
                current_node = current_node + neighbour
            else:
                current_node = neighbour + current_node
            path >>= 1
        return current_node.value == self.root.value

    async def compute_consistency_proof(self, old_width: int) -> Sequence[MerkleNode]:
        return [
            await self.calculate_node(*node_address)
            for node_address in self.consistency_proof_node_addresses(
                old_width, self.width
            )
        ]

    def verify_consistency_proof(
        self, old_tree: AbstractAsyncMerkleTree, proof: Sequence[MerkleNode]
    ) -> bool:
        if old_tree.width == self.width:
            return old_tree.root.value == self.root.value

        proof_addresses = list(
            self.consistency_proof_node_addresses(old_tree.width, self.width)
        )

        if len(proof_addresses) != len(proof):
            return False

        nodes: List[MerkleNode] = []

        if 2 ** math.floor(math.log2(old_tree.width)) == old_tree.width:
            # Add old tree as knowledge, to the start of the ordered dict
            nodes.append(old_tree.root)

        nodes.extend(proof)

        old_path = old_tree.width - 1
        new_path = self.width - 1
        while old_path & 1:
            old_path >>= 1
            new_path >>= 1

        otree = ntree = nodes[0]
        for node in nodes[1:]:
            if new_path == 0:
                return False
            if old_path & 1 or old_path == new_path:
                otree = node + otree
                ntree = node + ntree
                while not old_path & 1 and old_path > 0:
                    old_path >>= 1
                    new_path >>= 1
            else:
                ntree = ntree + node
            old_path >>= 1
            new_path >>= 1

        return (
            new_path == 0
            and otree.value == old_tree.root.value
            and ntree.value == self.root.value
        )

    @classmethod
    async def from_sequence(
        cls: AbstractAsyncMerkleTree, values: Iterable[bytes]
    ) -> AbstractAsyncMerkleTree:
        """Efficiently calculates the entire Merkle tree for a sequence of raw values."""
        stack: List[MerkleNode] = []
        full_index: Dict[Tuple[int, int], MerkleNode] = {}

        for i, value in enumerate(values):
            while len(stack) > 1 and stack[-2].height == stack[-1].height:
                stack[-2] = stack[-2] + stack[-1]
                del stack[-1]
                full_index[(stack[-1].start, stack[-1].end)] = stack[-1]
            stack.append(cls.NODE_CLASS.from_leaf(i, value))
            full_index[(stack[-1].start, stack[-1].end)] = stack[-1]

        while len(stack) > 1:
            stack[-2] = stack[-2] + stack[-1]
            del stack[-1]
            full_index[(stack[-1].start, stack[-1].end)] = stack[-1]

        return_node = (
            stack[0]
            if stack
            else MerkleNode(0, 0, cls.NODE_CLASS.hash_function().digest())
        )
        return await cls._from_sequence_with_seed(return_node, full_index)

    @classmethod
    async def _from_sequence_with_seed(
        cls, root: MerkleNode, index: Optional[Dict[Tuple[int, int], MerkleNode]] = None
    ):
        # Should be overridden in subclasses to store the index in cache
        return cls(root=root)

    @classmethod
    def from_root_value(cls, width: int, root_value: bytes) -> AbstractAsyncMerkleTree:
        return cls(root=MerkleNode(0, width, root_value))


class AbstractAsyncCachingMerkleTree(AbstractAsyncMerkleTree):
    @abstractmethod
    async def _getc(self, key: Tuple[int, int]) -> Optional[MerkleNode]:
        raise NotImplementedError()

    @abstractmethod
    async def _setc(self, key: Tuple[int, int], value: MerkleNode):
        raise NotImplementedError()

    async def seed(self, data: Dict[Tuple[int, int], MerkleNode]):
        raise NotImplementedError()

    @classmethod
    async def _from_sequence_with_seed(
        cls, root: MerkleNode, index: Optional[Dict[Tuple[int, int], MerkleNode]] = None
    ):
        retval = cls(root=root)
        await retval.seed(index)
        return retval

    async def calculate_node(self, start: int, end: int) -> MerkleNode:
        key = (start, end)
        if (retval := await self._getc(key)) is not None:
            return retval

        retval = await super().calculate_node(start, end)
        await self._setc(key, retval)
        return retval


class DictCachingMerkleTree(AbstractAsyncCachingMerkleTree):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._d: Dict[Tuple[int, int], MerkleNode] = {}

    async def fetch_leaf_data(self, position: int) -> MerkleNode:
        raise NotImplementedError()

    async def seed(self, data: Dict[Tuple[int, int], MerkleNode]):
        self._d.update(data)

    async def _getc(self, key: Tuple[int, int]) -> Optional[MerkleNode]:
        return self._d.get(key, None)

    async def _setc(self, key: Tuple[int, int], value: MerkleNode):
        self._d[key] = value
