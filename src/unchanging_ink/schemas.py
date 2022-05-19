import base64
import datetime
import uuid
from dataclasses import asdict, dataclass, field
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


class HashMixin:
    def calculate_hash(self) -> bytes:
        return sha512(self.to_cbor()).digest()


@dataclass
class TimestampRequest(CBORMixin, JSONMixin):
    data: str
    options: list[str] = field(default_factory=list)


@dataclass
class TimestampStructure(HashMixin, CBORMixin):
    data: str
    timestamp: str
    typ: str = "ts"
    version: str = "1"

    def calculate_hash(self) -> bytes:
        return sha512(self.to_cbor()).digest()


@dataclass
class IntervalProofStructure(CBORMixin, JSONMixin):
    a: int
    path: list[bytes]
    itmh: bytes
    mth: str

    def as_json_data(self):
        data = asdict(self)
        data["path"] = [base64.b64encode(x).decode() for x in data["path"]]
        data["itmh"] = base64.b64encode(data["itmh"]).decode() if data["itmh"] else None
        return data


@dataclass
class Timestamp(CBORMixin, JSONMixin):
    hash: bytes
    timestamp: str
    typ: str = "ts"
    version: str = "1"
    proof: Optional[IntervalProofStructure] = None

    def __post_init__(self):
        if isinstance(self.proof, bytes):
            self.proof = IntervalProofStructure.from_cbor(self.proof)

    def as_json_data(self):
        data = asdict(self)
        data["hash"] = base64.b64encode(data["hash"]).decode()
        if data["proof"]:
            if "itmh" in data["proof"]:
                data["proof"]["itmh"] = base64.b64encode(data["proof"]["itmh"]).decode()
            if "path" in data["proof"]:
                data["proof"]["path"] = [
                    base64.b64encode(x).decode() for x in data["proof"]["path"]
                ]
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
class IntervalTreeHead(HashMixin, CBORMixin, JSONMixin):
    interval: int
    timestamp: str
    itmh: bytes
    version: str = "1"
    typ: str = "it"

    def as_json_data(self):
        data = asdict(self)
        data["itmh"] = base64.b64encode(data["itmh"]).decode()
        return data

    @classmethod
    def from_row(cls, row):
        return cls(interval=row.id, timestamp=row.timestamp, itmh=row.itmh)


@dataclass
class MerkleTreeHead(CBORMixin, JSONMixin):
    interval: int
    mth: bytes
    version: str = "1"

    def as_json_data(self):
        data = asdict(self)
        data["mth"] = base64.b64encode(data["mth"]).decode()
        return data


@dataclass
class MerkleTreeConsistencyProof(CBORMixin, JSONMixin):
    old_interval: int
    new_interval: int
    nodes: list[bytes]
    version: str = "1"

    def as_json_data(self):
        data = asdict(self)
        data["nodes"] = [base64.b64encode(x).decode() for x in data["nodes"]]
        return data
