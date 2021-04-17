from __future__ import annotations

import math
from dataclasses import dataclass, field
from hashlib import sha512
from typing import Iterable, List, Dict, Tuple

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
    height: int = field(init=False)

    def __post_init__(self):
        self.height = int(math.ceil(math.log2(self.end - self.start + 1)))

    @classmethod
    def combine(cls: MerkleNode, n1: MerkleNode, n2: MerkleNode) -> MerkleNode:
        assert n1.end + 1 == n2.start
        return MerkleNode(
            n1.start, n2.end, sha512(b"\x01" + n1.value + n2.value).digest()
        )

    @classmethod
    def from_leaf(cls: MerkleNode, index: int, value: bytes) -> MerkleNode:
        return MerkleNode(index, index, sha512(b"\x00" + value).digest())

    @classmethod
    def from_sequence(
        cls: MerkleNode, values: Iterable[bytes]
    ) -> Tuple[MerkleNode, Dict[Tuple[int, int], MerkleNode]]:
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

        return stack[0], full_index


def setup_crypto(app: Sanic):
    app.ctx.crypto = Signer()
