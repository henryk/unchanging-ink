from __future__ import annotations

import math
from dataclasses import dataclass, field
from hashlib import sha512
from typing import Dict, Iterable, List, Tuple, Optional, Sequence

from nacl.encoding import Base64Encoder
from nacl.signing import SigningKey
from sanic import Sanic


class Signer:
    def __init__(self):
        self.key: SigningKey = SigningKey.generate()
        self.kid = "Exp:" + self.key.verify_key.encode(Base64Encoder).decode("us-ascii")

    def sign(self, data: bytes) -> bytes:
        return self.key.sign(data).signature


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

    @classmethod
    def combine(cls: MerkleNode, n1: MerkleNode, n2: MerkleNode) -> MerkleNode:
        assert n1.end == n2.start
        return MerkleNode(
            n1.start, n2.end, cls.hash_function(b"\x01" + n1.value + n2.value).digest()
        )

    @classmethod
    def from_leaf(cls: MerkleNode, index: int, value: bytes) -> MerkleNode:
        return MerkleNode(index, index+1, cls.hash_function(b"\x00" + value).digest())

    @classmethod
    def from_sequence_with_index(
        cls: MerkleNode, values: Iterable[bytes]
    ) -> Tuple[MerkleNode, Dict[Tuple[int, int], MerkleNode]]:
        """Efficiently calculates the entire Merkle tree for a sequence of raw values.

        Returns the root node and an index dictionary mapping (start, end) to nodes. (start inclusive, end exclusive)"""
        stack: List[MerkleNode] = []
        full_index: Dict[Tuple[int, int], MerkleNode] = {}

        for i, value in enumerate(values):
            while len(stack) > 1 and stack[-2].height == stack[-1].height:
                stack[-2] = cls.combine(stack[-2], stack[-1])
                del stack[-1]
                full_index[(stack[-1].start, stack[-1].end)] = stack[-1]
            stack.append(cls.from_leaf(i, value))
            full_index[(stack[-1].start, stack[-1].end)] = stack[-1]

        while len(stack) > 1:
            stack[-2] = cls.combine(stack[-2], stack[-1])
            del stack[-1]
            full_index[(stack[-1].start, stack[-1].end)] = stack[-1]

        return_node = stack[0] if stack else MerkleNode(0, 0, cls.hash_function().digest())
        return return_node, full_index

    @classmethod
    def path_proof(cls: MerkleNode, tree_index: Dict[Tuple[int, int], MerkleNode], x: int, n: int) -> Tuple[int, Sequence[MerkleNode]]:
        current_read_bit: int = 1
        current_write_bit: int = 1
        current_width: int = 1
        path: int = 0
        neighbours: List[MerkleNode] = []

        mytree: MerkleNode = tree_index[(x, x+1)]
        while not (mytree.start == 0 and mytree.end == n):
            if mytree.start & current_read_bit == 0:
                # This is the left side
                otherend = min(n, mytree.end + current_width)
                if mytree.end != otherend:
                    othertree = tree_index[(mytree.end, otherend)]
                else:
                    othertree = None
                # Do not OR in current_write_bit
            else:
                # Right side
                otherstart = max(0, mytree.start - current_width)
                if mytree.start != otherstart:
                    othertree = tree_index[(otherstart, mytree.start)]
                    path |= current_write_bit
                else:
                    othertree = None

            current_width *= 2
            current_read_bit <<= 1

            if othertree is None:
                # There is no other side
                continue

            if othertree.start == 0 and othertree.end == n:
                break

            current_write_bit <<= 1
            neighbours.append(othertree)

            mytree = tree_index[(min(mytree.start, othertree.start), max(mytree.end, othertree.end))]

        return path, neighbours

    @classmethod
    def verify_proof(cls, head_node: MerkleNode, leaf_node: MerkleNode, path: int, neighbours: Sequence[MerkleNode]) -> bool:
        current_node = leaf_node
        for neighbour in neighbours:
            if path & 1 == 0:
                # Left side
                current_node = MerkleNode.combine(current_node, neighbour)
            else:
                current_node = MerkleNode.combine(neighbour, current_node)
            path >>= 1
        return current_node.value == head_node.value


@dataclass
class MerkleTree:
    width: int
    nodes: Dict[Tuple[int, int], MerkleNode]

    @property
    def root(self):
        if self.width > 0:
            return self.nodes[(0, self.width)]
        raise ValueError

    @classmethod
    def from_root(cls: MerkleTree, root: MerkleNode) -> MerkleTree:
        return cls(root.end - root.start, {(root.start, root.end): root})

    @classmethod
    def from_sequence(cls: MerkleTree, values: Iterable[bytes]) -> MerkleTree:
        root, nodes = MerkleNode.from_sequence_with_index(values)
        return cls(root.end - root.start, nodes)

    def proof_for(self, x: int) -> Tuple[int, Sequence[MerkleNode]]:
        return MerkleNode.path_proof(self.nodes, x, self.width)

    def verify_proof(self, leaf_node: MerkleNode, path: int, neighbours: Sequence[MerkleNode]) -> bool:
        return MerkleNode.verify_proof(self.root, leaf_node, path, neighbours)


def setup_crypto(app: Sanic):
    app.ctx.crypto = Signer()

