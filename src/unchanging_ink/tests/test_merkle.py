import pytest

from unchanging_ink.crypto import MerkleNode, MerkleTree


def test_tree_none():
    a, idx = MerkleNode.from_sequence_with_index([])
    assert a.value == bytes.fromhex("cf83e1357eefb8bdf1542850d66d8007d620e4050b5715dc83f4a921d36ce9ce47d0d13c5d85f2b0ff8318d2877eec2f63b931bd47417a81a538327af927da3e")
    assert a.height == 0


def test_tree_one():
    a, idx = MerkleNode.from_sequence_with_index([b""])
    assert a.value == bytes.fromhex("b8244d028981d693af7b456af8efa4cad63d282e19ff14942c246e50d9351d22704a802a71c3580b6370de4ceb293c324a8423342557d4e5c38438f0e36910ee")
    assert a.height == 1


def test_tree_two():
    a, idx = MerkleNode.from_sequence_with_index([b"", b""])
    assert a.value == bytes.fromhex("1a034e5f1603a9d3fec55238936880505ddf93facd23b682c10f6b84c5d5397da7fbdc2153ce0035bc0ba49424cbf73fe277129ca88a699d6454a2237508459e")
    assert a.height == 2


def test_tree_three():
    a, idx = MerkleNode.from_sequence_with_index([b"", b"", b""])
    assert a.value == bytes.fromhex("fecee1acb8cf134ebcb4f14f793c0d4e2d05f9d3f761e9fe8e33f8c1d6570ed9644f2691b9afbcc268836503ef723f8af4bb445b8fc8172530fdbada8cadf8e0")
    assert a.height == 3


def test_tree_four():
    a, idx = MerkleNode.from_sequence_with_index([b"", b"", b"", b""])
    assert a.value == bytes.fromhex("ad3f8edebd8a45f301e62bcb2f472da77a329126425fe53f9126cd01db0983400a56e2deb9e984c8a69dc0181d2093db9186b5d6bcbf443e6a9d33a211a5b301")
    assert a.height == 3
    assert idx[(0, 1)].value == bytes.fromhex("b8244d028981d693af7b456af8efa4cad63d282e19ff14942c246e50d9351d22704a802a71c3580b6370de4ceb293c324a8423342557d4e5c38438f0e36910ee")


def test_tree_four_content():
    a, idx = MerkleNode.from_sequence_with_index([b"A", b"BB", b"CCC", b"DDDD"])
    assert a.value == bytes.fromhex("3b5d486f014f22858d9d87021b3c0f707009969895eeffe8e0642d81aea3906764d10ad2ff0b961fcf07d83eabd8d9eaa7242cd4a7aacde5ccb1e3c1b9a2ff94")
    assert idx[(0, 4)] == a


@pytest.fixture(scope='session')
def tree_index_width_7():
    _, idx = MerkleNode.from_sequence_with_index([str(i).encode() for i in range(7)])
    return idx


def test_proof_simple_7_0(tree_index_width_7):
    path, proof = MerkleNode.path_proof(tree_index_width_7, 0, 7)
    assert path == 0
    assert proof == [
        tree_index_width_7[(1, 2)],
        tree_index_width_7[(2, 4)],
        tree_index_width_7[(4, 7)],
    ]


def test_proof_simple_7_1(tree_index_width_7):
    path, proof = MerkleNode.path_proof(tree_index_width_7, 1, 7)
    assert path == 1
    assert proof == [
        tree_index_width_7[(0, 1)],
        tree_index_width_7[(2, 4)],
        tree_index_width_7[(4, 7)],
    ]


def test_proof_simple_7_6(tree_index_width_7):
    path, proof = MerkleNode.path_proof(tree_index_width_7, 6, 7)
    assert path == 3
    assert proof == [
        tree_index_width_7[(4, 6)],
        tree_index_width_7[(0, 4)],
    ]


@pytest.mark.parametrize("target,length", [(i, n) for n in range(1, 17) for i in range(n)])
def test_proof_verify(target, length):
    head_node, idx = MerkleNode.from_sequence_with_index([str(i).encode() for i in range(length)])
    leaf_node = idx[(target, target+1)]
    path, proof = MerkleNode.path_proof(idx, target, length)
    assert MerkleNode.verify_proof(head_node, leaf_node, path, proof)


@pytest.fixture(scope='session')
def merkle_tree_7() -> MerkleTree:
    return MerkleTree.from_sequence([str(i).encode() for i in range(7)])


@pytest.fixture(scope='session')
def merkle_tree_11() -> MerkleTree:
    return MerkleTree.from_sequence([str(i).encode() for i in range(11)])


def test_tree_verify(merkle_tree_11):
    path, proof = merkle_tree_11.compute_inclusion_proof(9)

    checking_tree = MerkleTree.from_root(MerkleNode(0, 11, merkle_tree_11.root.value))
    leaf_node = MerkleNode.from_leaf(9, str(9).encode())

    assert checking_tree.verify_inclusion_proof(leaf_node, path, proof)


def test_consistency_proof_1(merkle_tree_7):
    proof = merkle_tree_7.compute_consistency_proof(3)

    assert [(n.start, n.end) for n in proof] == [(0, 2), (2, 3), (3, 4), (4, 7)]


def test_consistency_proof_2(merkle_tree_7):
    proof = merkle_tree_7.compute_consistency_proof(4)

    assert [(n.start, n.end) for n in proof] == [(4, 7)]


def test_consistency_proof_3(merkle_tree_7):
    proof = merkle_tree_7.compute_consistency_proof(6)

    assert [(n.start, n.end) for n in proof] == [(0, 4), (4, 6), (6, 7)]
