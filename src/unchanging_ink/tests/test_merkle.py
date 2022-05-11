from unchanging_ink.crypto import MerkleNode


def test_tree_none():
    a, idx = MerkleNode.from_sequence([])
    assert a.value == bytes.fromhex("cf83e1357eefb8bdf1542850d66d8007d620e4050b5715dc83f4a921d36ce9ce47d0d13c5d85f2b0ff8318d2877eec2f63b931bd47417a81a538327af927da3e")


def test_tree_one():
    a, idx = MerkleNode.from_sequence([b""])
    assert a.value == bytes.fromhex("b8244d028981d693af7b456af8efa4cad63d282e19ff14942c246e50d9351d22704a802a71c3580b6370de4ceb293c324a8423342557d4e5c38438f0e36910ee")


def test_tree_two():
    a, idx = MerkleNode.from_sequence([b"", b""])
    assert a.value == bytes.fromhex("1a034e5f1603a9d3fec55238936880505ddf93facd23b682c10f6b84c5d5397da7fbdc2153ce0035bc0ba49424cbf73fe277129ca88a699d6454a2237508459e")


def test_tree_three():
    a, idx = MerkleNode.from_sequence([b"", b"", b""])
    assert a.value == bytes.fromhex("fecee1acb8cf134ebcb4f14f793c0d4e2d05f9d3f761e9fe8e33f8c1d6570ed9644f2691b9afbcc268836503ef723f8af4bb445b8fc8172530fdbada8cadf8e0")


def test_tree_four():
    a, idx = MerkleNode.from_sequence([b"", b"", b"", b""])
    assert a.value == bytes.fromhex("ad3f8edebd8a45f301e62bcb2f472da77a329126425fe53f9126cd01db0983400a56e2deb9e984c8a69dc0181d2093db9186b5d6bcbf443e6a9d33a211a5b301")


def test_tree_four_content():
    a, idx = MerkleNode.from_sequence([b"A", b"BB", b"CCC", b"DDDD"])
    assert a.value == bytes.fromhex("3b5d486f014f22858d9d87021b3c0f707009969895eeffe8e0642d81aea3906764d10ad2ff0b961fcf07d83eabd8d9eaa7242cd4a7aacde5ccb1e3c1b9a2ff94")

