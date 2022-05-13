from __future__ import annotations

import math
from collections import OrderedDict
from dataclasses import dataclass, field
from hashlib import sha512
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


def consistency_proof_nodes(old_width, new_width) -> Iterable[Tuple[int, int]]:
    yield from _consistency_proof_subnodes(old_width, new_width, True)


def _consistency_proof_subnodes(
    m: int, n: int, flag: bool, _o: int = 0
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
            yield from _consistency_proof_subnodes(m, k, flag, _o)
            yield _o + k, _o + n
        else:
            yield _o + 0, _o + k
            yield from _consistency_proof_subnodes(m - k, n - k, False, _o + k)


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
        return MerkleNode(index, index + 1, cls.hash_function(b"\x00" + value).digest())

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

        return_node = (
            stack[0] if stack else MerkleNode(0, 0, cls.hash_function().digest())
        )
        return return_node, full_index

    @classmethod
    def path_proof(
        cls: MerkleNode, tree_index: Dict[Tuple[int, int], MerkleNode], x: int, n: int
    ) -> Tuple[int, Sequence[MerkleNode]]:
        current_read_bit: int = 1
        current_write_bit: int = 1
        current_width: int = 1
        path: int = 0
        neighbours: List[MerkleNode] = []

        mytree: MerkleNode = tree_index[(x, x + 1)]
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

            mytree = tree_index[
                (min(mytree.start, othertree.start), max(mytree.end, othertree.end))
            ]

        return path, neighbours

    @classmethod
    def verify_proof(
        cls,
        head_node: MerkleNode,
        leaf_node: MerkleNode,
        path: int,
        neighbours: Sequence[MerkleNode],
    ) -> bool:
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

    def compute_inclusion_proof(self, x: int) -> Tuple[int, Sequence[MerkleNode]]:
        return MerkleNode.path_proof(self.nodes, x, self.width)

    def verify_inclusion_proof(
        self, leaf_node: MerkleNode, path: int, neighbours: Sequence[MerkleNode]
    ) -> bool:
        return MerkleNode.verify_proof(self.root, leaf_node, path, neighbours)

    def compute_consistency_proof(self, old_width) -> Sequence[MerkleNode]:
        return [
            self.nodes[node_address]
            for node_address in consistency_proof_nodes(old_width, self.width)
        ]


def verify_consistency_proof(old_width: int, old_head: bytes, new_width: int, new_head: bytes, proof: List[bytes]) -> bool:
    proof_addresses = list(consistency_proof_nodes(old_width, new_width))

    if len(proof_addresses) != len(proof):
        return False

    nodes = OrderedDict(zip(proof_addresses, proof))

    # Start at end of the old tree, move left until the old tree is fully covered
    old_tree = nodes[[na for na in nodes.keys() if na[1] == old_width][0]]
    while old_tree.start != 0:
        left_na = [na for na in nodes.keys() if na[1] == old_tree.start][0]
        old_tree = MerkleNode.combine(nodes[left_na], old_tree)

    if not (old_tree.start == 0 and old_tree.end == old_width and old_tree.value == old_head):
        return False

    # Add old tree as knowledge
    nodes[(0, old_width)] = MerkleNode(start=0, end=old_width, value=old_head)

    # Start at the node that is that the right edge of the old tree. Then work upwards
    new_tree = nodes[[na for na in nodes.keys() if na[1] == old_width][0]]
    bit = 1
    while not (new_tree.start == 0 and new_tree.end == new_width):
        if new_tree.start & bit == 0:
            # This is the left side. Find right side
            right_na = [na for na in nodes.keys() if na[0] == new_tree.end][0]
            new_tree = MerkleNode.combine(new_tree, nodes[right_na])
        else:
            # This is the right side. Find left side
            left_na = [na for na in nodes.keys() if na[1] == new_tree.start][0]
            new_tree = MerkleNode.combine(nodes[left_na], new_tree)
        bit <<= 1

    if not (new_tree.start == 0 and new_tree.end == new_width and new_tree.value == new_head):
        return False

    return True
