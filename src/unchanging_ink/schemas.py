import datetime
from dataclasses import dataclass, asdict
from typing import Optional

import cbor2
import orjson


class CBORMixin:
    @classmethod
    def from_cbor(cls, data: bytes):
        return cls(**cbor2.loads(data))

    def to_cbor(self) -> bytes:
        return cbor2.dumps(asdict(self), canonical=True)


class JSONMixin:
    @classmethod
    def from_json(cls, data: bytes):
        return cls(**orjson.loads(data))

    def to_json(self) -> bytes:
        return orjson.dumps(asdict(self))


@dataclass
class TimestampRequest(CBORMixin, JSONMixin):
    data: str
    options: list[str]


@dataclass
class TimestampStructure(CBORMixin):
    data: str
    timestamp: datetime.datetime
    typ: str = "ts"
    version: str = "1"


@dataclass
class IntervalProofStructure:
    mth: str
    itmh: bytes
    a: int
    path: list[bytes]


@dataclass
class Timestamp(CBORMixin, JSONMixin):
    hash: bytes
    timestamp: datetime.datetime
    typ: str = "ts"
    version: str = "1"
    proof: Optional[IntervalProofStructure] = None


@dataclass
class IntervalTreeHead:
    version: int
    interval: int
    timestamp: str
    itmh: bytes


@dataclass
class MerkleTreeHead:
    version: int
    interval: int
    mth: bytes


@dataclass
class MerkleTreeConsistencyProof:
    version: int
    old_interval: int
    new_interval: int
    nodes: list[bytes]
