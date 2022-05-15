import pytest

from unchanging_ink.crypto.merkle import (AbstractAsyncMerkleTree,
                                          DictCachingMerkleTree, MerkleNode)


class EmptyMerkleTreeUncached(AbstractAsyncMerkleTree):
    async def fetch_leaf_data(self, position: int) -> bytes:
        raise NotImplementedError()


class StandardMerkleTreeUncached(AbstractAsyncMerkleTree):
    async def fetch_leaf_data(self, position: int) -> bytes:
        return str(position).encode()


@pytest.fixture(scope="session")
def merkle_tree_7():
    return StandardMerkleTreeUncached(width=7)


@pytest.fixture
def merkle_tree_11() -> AbstractAsyncMerkleTree:
    return StandardMerkleTreeUncached(width=11)


async def test_tree_none():
    t = await EmptyMerkleTreeUncached.from_sequence([])
    assert t.root.value == bytes.fromhex(
        "cf83e1357eefb8bdf1542850d66d8007d620e4050b5715dc83f4a921d36ce9ce47d0d13c5d85f2b0ff8318d2877eec2f63b931bd47417a81a538327af927da3e "
    )
    assert t.root.height == 0


async def test_tree_one():
    t = await EmptyMerkleTreeUncached.from_sequence([b""])
    assert t.root.value == bytes.fromhex(
        "b8244d028981d693af7b456af8efa4cad63d282e19ff14942c246e50d9351d22704a802a71c3580b6370de4ceb293c324a8423342557d4e5c38438f0e36910ee"
    )
    assert t.root.height == 1


async def test_tree_two():
    t = await EmptyMerkleTreeUncached.from_sequence([b"", b""])
    assert t.root.value == bytes.fromhex(
        "1a034e5f1603a9d3fec55238936880505ddf93facd23b682c10f6b84c5d5397da7fbdc2153ce0035bc0ba49424cbf73fe277129ca88a699d6454a2237508459e"
    )
    assert t.root.height == 2


async def test_tree_three():
    t = await EmptyMerkleTreeUncached.from_sequence([b"", b"", b""])
    assert t.root.value == bytes.fromhex(
        "fecee1acb8cf134ebcb4f14f793c0d4e2d05f9d3f761e9fe8e33f8c1d6570ed9644f2691b9afbcc268836503ef723f8af4bb445b8fc8172530fdbada8cadf8e0"
    )
    assert t.root.height == 3


async def test_tree_four():
    t = await DictCachingMerkleTree.from_sequence([b"", b"", b"", b""])
    assert t.root.value == bytes.fromhex(
        "ad3f8edebd8a45f301e62bcb2f472da77a329126425fe53f9126cd01db0983400a56e2deb9e984c8a69dc0181d2093db9186b5d6bcbf443e6a9d33a211a5b301"
    )
    assert t.root.height == 3
    assert t._d[(0, 1)].value == bytes.fromhex(
        "b8244d028981d693af7b456af8efa4cad63d282e19ff14942c246e50d9351d22704a802a71c3580b6370de4ceb293c324a8423342557d4e5c38438f0e36910ee"
    )


async def test_tree_four_content():
    t = await DictCachingMerkleTree.from_sequence([b"A", b"BB", b"CCC", b"DDDD"])
    assert t.root.value == bytes.fromhex(
        "3b5d486f014f22858d9d87021b3c0f707009969895eeffe8e0642d81aea3906764d10ad2ff0b961fcf07d83eabd8d9eaa7242cd4a7aacde5ccb1e3c1b9a2ff94"
    )
    assert t._d[(0, 4)] == t.root


async def test_proof_simple_7_0(merkle_tree_7):
    path, proof = await merkle_tree_7.compute_inclusion_proof(0)
    assert path == 0
    assert proof == [
        await merkle_tree_7.calculate_node(1, 2),
        await merkle_tree_7.calculate_node(2, 4),
        await merkle_tree_7.calculate_node(4, 7),
    ]


async def test_proof_simple_7_1(merkle_tree_7):
    path, proof = await merkle_tree_7.compute_inclusion_proof(1)
    assert path == 1
    assert proof == [
        await merkle_tree_7.calculate_node(0, 1),
        await merkle_tree_7.calculate_node(2, 4),
        await merkle_tree_7.calculate_node(4, 7),
    ]


async def test_proof_simple_7_6(merkle_tree_7):
    path, proof = await merkle_tree_7.compute_inclusion_proof(6)
    assert path == 3
    assert proof == [
        await merkle_tree_7.calculate_node(4, 6),
        await merkle_tree_7.calculate_node(0, 4),
    ]


@pytest.mark.parametrize(
    "target,length", [(i, n) for n in range(1, 17) for i in range(n)]
)
async def test_proof_verify(target, length):
    tree = await DictCachingMerkleTree.from_sequence(
        [str(i).encode() for i in range(length)]
    )
    leaf_node = await tree.calculate_node(target, target + 1)
    path, proof = await tree.compute_inclusion_proof(target)
    assert tree.verify_inclusion_proof(leaf_node, path, proof)


async def test_tree_verify(merkle_tree_11):
    path, proof = await merkle_tree_11.compute_inclusion_proof(9)

    checking_tree = EmptyMerkleTreeUncached.from_root_value(
        width=11,
        root_value=(await merkle_tree_11.calculate_node(0, merkle_tree_11.width)).value,
    )
    leaf_node = MerkleNode.from_leaf(9, str(9).encode())

    assert checking_tree.verify_inclusion_proof(leaf_node, path, proof)


async def test_consistency_proof_nodes_1():
    proof_node_addresses = AbstractAsyncMerkleTree.consistency_proof_node_addresses(
        3, 7
    )

    assert list(proof_node_addresses) == [(2, 3), (3, 4), (0, 2), (4, 7)]


async def test_consistency_proof_nodes_2():
    proof = AbstractAsyncMerkleTree.consistency_proof_node_addresses(4, 7)

    assert list(proof) == [(4, 7)]


async def test_consistency_proof_nodes_3():
    proof = AbstractAsyncMerkleTree.consistency_proof_node_addresses(6, 7)
    assert list(proof) == [(4, 6), (6, 7), (0, 4)]


async def test_consistency_proof_verify_1(merkle_tree_7, merkle_tree_11):
    proof = await merkle_tree_11.compute_consistency_proof(merkle_tree_7.width)

    new_tree_11 = EmptyMerkleTreeUncached.from_root_value(
        width=11,
        root_value=(await merkle_tree_11.calculate_node(0, merkle_tree_11.width)).value,
    )
    assert new_tree_11.verify_consistency_proof(
        EmptyMerkleTreeUncached.from_root_value(
            width=7,
            root_value=(
                await merkle_tree_7.calculate_node(0, merkle_tree_7.width)
            ).value,
        ),
        proof,
    )


@pytest.mark.parametrize(
    "old_width,new_width", [(o, n) for n in range(1, 17) for o in range(1, n + 1)]
)
async def test_consistency_proof_verify(old_width, new_width):
    old_head = (
        await StandardMerkleTreeUncached(width=old_width).calculate_node(0, old_width)
    ).value
    new_tree = StandardMerkleTreeUncached(width=new_width)
    new_head = (await new_tree.calculate_node(0, new_width)).value

    proof = await new_tree.compute_consistency_proof(old_width)

    assert EmptyMerkleTreeUncached.from_root_value(
        width=new_width, root_value=new_head
    ).verify_consistency_proof(
        EmptyMerkleTreeUncached.from_root_value(width=old_width, root_value=old_head),
        proof,
    )
