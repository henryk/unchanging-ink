from __future__ import annotations

from nacl.encoding import Base64Encoder
from nacl.signing import SigningKey
from sanic import Sanic

from .merkle import (AbstractAsyncCachingMerkleTree, AbstractAsyncMerkleTree,
                     DictCachingMerkleTree, MerkleNode)


class Signer:
    def __init__(self):
        self.key: SigningKey = SigningKey.generate()
        self.kid = "Exp:" + self.key.verify_key.encode(Base64Encoder).decode("us-ascii")

    def sign(self, data: bytes) -> bytes:
        return self.key.sign(data).signature


def setup_crypto(app: Sanic):
    app.ctx.crypto = Signer()
