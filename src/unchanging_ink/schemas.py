from dataclasses import dataclass


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
