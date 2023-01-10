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
        "a7ffc6f8bf1ed76651c14756a061d662f580ff4de43b49fa82d80a4b80f8434a"
    )
    assert t.root.height == 0


async def test_tree_one():
    t = await EmptyMerkleTreeUncached.from_sequence([b""])
    assert t.root.value == bytes.fromhex(
        "5d53469f20fef4f8eab52b88044ede69c77a6a68a60728609fc4a65ff531e7d0"
    )
    assert t.root.height == 1


async def test_tree_two():
    t = await EmptyMerkleTreeUncached.from_sequence([b"", b""])
    assert t.root.value == bytes.fromhex(
        "8b29b8678bd3e23f381c527ba2f27d06829d1c5e785270f038a138318a15b527"
    )
    assert t.root.height == 2


async def test_tree_three():
    t = await EmptyMerkleTreeUncached.from_sequence([b"", b"", b""])
    assert t.root.value == bytes.fromhex(
        "b1d31639b720c4e985a01148b2309ea245db0204484a7afa295e939022aef754"
    )
    assert t.root.height == 3


async def test_tree_four():
    t = await DictCachingMerkleTree.from_sequence([b"", b"", b"", b""])
    assert t.root.value == bytes.fromhex(
        "57ab20bc2264fb5993323d4166270415f3b967286e4736769fac4b91137fba5c"
    )
    assert t.root.height == 3
    assert t._d[(0, 1)].value == bytes.fromhex(
        "5d53469f20fef4f8eab52b88044ede69c77a6a68a60728609fc4a65ff531e7d0"
    )


async def test_tree_four_content():
    t = await DictCachingMerkleTree.from_sequence([b"A", b"BB", b"CCC", b"DDDD"])
    assert t.root.value == bytes.fromhex(
        "83a02c3bd02ecb504a41cbebf3f618e91d67d289d35db132e66a6b475db7facd"
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
