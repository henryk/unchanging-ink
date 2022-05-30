import base64
import uuid
from dataclasses import asdict, dataclass
from hashlib import sha3_256
from typing import Optional, TypeVar

import cbor2
import orjson

ConcreteTime = TypeVar("ConcreteTime", bound=str)
CompactRepr = TypeVar("CompactRepr", bound=str)


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
        return sha3_256(self.to_cbor()).digest()


@dataclass
class TimestampRequest(CBORMixin, JSONMixin):
    data: str


@dataclass
class TimestampStructure(HashMixin, CBORMixin):
    data: str
    timestamp: ConcreteTime
    typ: str = "ts"
    version: str = "1"

    def calculate_hash(self) -> bytes:
        return sha3_256(self.to_cbor()).digest()


@dataclass
class IntervalProofStructure(CBORMixin, JSONMixin):
    a: int
    path: list[bytes]
    ith: bytes
    mth: CompactRepr

    def as_json_data(self):
        data = asdict(self)
        data["path"] = [base64.b64encode(x).decode() for x in data["path"]]
        data["ith"] = base64.b64encode(data["ith"]).decode() if data["ith"] else None
        return data


@dataclass
class Timestamp(CBORMixin, JSONMixin):
    hash: bytes
    timestamp: ConcreteTime
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
            if "ith" in data["proof"]:
                data["proof"]["ith"] = base64.b64encode(data["proof"]["ith"]).decode()
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

    @classmethod
    def from_dict(cls, row):
        return cls(**{k: v for (k, v) in row.items() if k not in ("tag",)})


@dataclass
class Interval(HashMixin, CBORMixin, JSONMixin):
    index: int
    timestamp: ConcreteTime
    ith: bytes
    version: str = "1"
    typ: str = "it"

    def as_json_data(self):
        data = asdict(self)
        data["ith"] = base64.b64encode(data["ith"]).decode()
        return data

    @classmethod
    def from_row(cls, row):
        return cls(index=row.id, timestamp=row.timestamp, ith=row.ith)


@dataclass
class MainTreeConsistencyProof(CBORMixin, JSONMixin):
    old_interval: int
    new_interval: int
    nodes: list[bytes]
    version: str = "1"

    def as_json_data(self):
        data = asdict(self)
        data["nodes"] = [base64.b64encode(x).decode() for x in data["nodes"]]
        return data


@dataclass
class MainHead(CBORMixin, JSONMixin):
    authority: str
    interval: Interval
    mth: bytes
    version: str = "1"
    proof: Optional[MainTreeConsistencyProof] = None

    def as_json_data(self):
        data = asdict(self)
        data["proof"] = self.proof.as_json_data() if self.proof else None
        data["interval"] = self.interval.as_json_data()
        data["mth"] = base64.b64encode(data["mth"]).decode()
        return data
