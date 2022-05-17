import base64
import datetime
import uuid
from dataclasses import dataclass, asdict, field
from hashlib import sha512
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

    def as_json_data(self):
        return asdict(self)

    def to_json(self) -> bytes:
        return orjson.dumps(self.as_json_data())


@dataclass
class TimestampRequest(CBORMixin, JSONMixin):
    data: str
    options: list[str] = field(default_factory=list)


@dataclass
class TimestampStructure(CBORMixin):
    data: str
    timestamp: datetime.datetime
    typ: str = "ts"
    version: str = "1"

    def calculate_hash(self) -> bytes:
        return sha512(self.to_cbor()).digest()


@dataclass
class IntervalProofStructure:
    mth: str
    itmh: bytes
    a: int
    path: list[bytes]


@dataclass
class Timestamp(CBORMixin, JSONMixin):
    hash: bytes
    timestamp: str
    typ: str = "ts"
    version: str = "1"
    proof: Optional[IntervalProofStructure] = None

    def as_json_data(self):
        data = asdict(self)
        data["hash"] = base64.encodebytes(data["hash"]).decode()
        del data["proof"]  # FIXME
        return data


@dataclass
class TimestampWithId(Timestamp):
    id: Optional[uuid.UUID] = None
    interval: Optional[int] = None

    def as_json_data(self):
        data = super().as_json_data()
        data["id"] = str(data["id"])
        return data


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
