"""Comprehensive tests for py-merkledrop."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from merkledrop import HashAlgo, MerkleAirdrop, keccak256
from merkledrop.core import hash_leaf


SAMPLE = [
    ("0x1111111111111111111111111111111111111111", 1000),
    ("0x2222222222222222222222222222222222222222", 500),
    ("0x3333333333333333333333333333333333333333", 250),
    ("0x4444444444444444444444444444444444444444", 125),
]


@pytest.mark.parametrize("algo", [HashAlgo.SHA256, HashAlgo.KECCAK256])
def test_roundtrip(algo: HashAlgo):
    airdrop = MerkleAirdrop.from_entries(SAMPLE, algo=algo)
    for addr, amt in SAMPLE:
        proof = airdrop.get_proof(addr, amt)
        assert airdrop.verify(addr, amt, proof)


@pytest.mark.parametrize("algo", [HashAlgo.SHA256, HashAlgo.KECCAK256])
def test_order_independent_root(algo: HashAlgo):
    a1 = MerkleAirdrop.from_entries(SAMPLE, algo=algo)
    a2 = MerkleAirdrop.from_entries(list(reversed(SAMPLE)), algo=algo)
    assert a1.root == a2.root
    assert a1.root_hex == a2.root_hex


def test_csv_roundtrip():
    with tempfile.TemporaryDirectory() as tmp:
        csv_path = Path(tmp) / "airdrop.csv"
        csv_path.write_text(
            "address,amount\n"
            "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa,100\n"
            "0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb,200\n"
            "0xcccccccccccccccccccccccccccccccccccccccc,300\n",
            encoding="utf-8",
        )
        airdrop = MerkleAirdrop.from_csv(csv_path)
        assert airdrop.size == 3
        proof = airdrop.get_proof("0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")
        assert airdrop.verify("0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", 100, proof)


def test_invalid_proof_rejected():
    airdrop = MerkleAirdrop.from_entries(SAMPLE)
    proof = airdrop.get_proof(SAMPLE[0][0], SAMPLE[0][1])
    if proof:
        proof = list(proof)
        proof[0] = "0x" + "00" * 32
    assert not airdrop.verify(SAMPLE[0][0], SAMPLE[0][1], proof)


def test_wrong_amount_rejected():
    airdrop = MerkleAirdrop.from_entries(SAMPLE)
    proof = airdrop.get_proof(SAMPLE[0][0], SAMPLE[0][1])
    assert not airdrop.verify(SAMPLE[0][0], SAMPLE[0][1] + 1, proof)


def test_export_and_stats():
    airdrop = MerkleAirdrop.from_entries(SAMPLE)
    proofs = airdrop.export_proofs()
    assert len(proofs) == 4
    stats = airdrop.stats()
    assert stats["recipients"] == 4
    assert stats["total_amount"] == 1875
    assert stats["min_amount"] == 125
    assert stats["max_amount"] == 1000


def test_generate_from_csv_writes_files():
    from merkledrop import generate_from_csv

    with tempfile.TemporaryDirectory() as tmp:
        csv_path = Path(tmp) / "data.csv"
        csv_path.write_text(
            "address,amount\n0x1111111111111111111111111111111111111111,42\n",
            encoding="utf-8",
        )
        root = generate_from_csv(csv_path, tmp)
        assert (Path(tmp) / "merkle_root.txt").read_text().strip() == root
        data = json.loads((Path(tmp) / "proofs.json").read_text())
        assert data["root"] == root
        assert data["count"] == 1


def test_keccak_known_vector():
    # Empty input Keccak-256
    # Official: c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470
    assert keccak256(b"").hex() == "c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470"


def test_duplicate_addresses_last_wins():
    entries = [
        ("0x1111111111111111111111111111111111111111", 100),
        ("0x1111111111111111111111111111111111111111", 999),
    ]
    airdrop = MerkleAirdrop.from_entries(entries)
    assert airdrop.size == 1
    assert airdrop.entries[0][1] == 999


def test_invalid_address_raises():
    with pytest.raises(ValueError):
        MerkleAirdrop.from_entries([("0x123", 1)])
