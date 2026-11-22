"""Tests for py-merkledrop."""

import json
import tempfile
from pathlib import Path

import pytest

from merkledrop import MerkleAirdrop, _hash_leaf


def test_basic_roundtrip():
    entries = [
        ("0x1111111111111111111111111111111111111111", 1000),
        ("0x2222222222222222222222222222222222222222", 500),
        ("0x3333333333333333333333333333333333333333", 250),
    ]
    airdrop = MerkleAirdrop.from_entries(entries)

    for addr, amt in entries:
        proof = airdrop.get_proof(addr, amt)
        assert airdrop.verify(addr, amt, proof)


def test_csv_roundtrip():
    with tempfile.TemporaryDirectory() as tmp:
        csv_path = Path(tmp) / "test.csv"
        csv_path.write_text(
            "address,amount\n"
            "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa,100\n"
            "0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb,200\n"
        )
        airdrop = MerkleAirdrop.from_csv(str(csv_path))
        assert airdrop.verify(
            "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            100,
            airdrop.get_proof("0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", 100),
        )


def test_invalid_proof_fails():
    entries = [("0x1111111111111111111111111111111111111111", 1000)]
    airdrop = MerkleAirdrop.from_entries(entries)
    proof = airdrop.get_proof(entries[0][0], entries[0][1])
    # Tamper
    if proof:
        proof[0] = "0x" + "00" * 32
    assert not airdrop.verify(entries[0][0], entries[0][1], proof)


def test_deterministic_root():
    entries = [
        ("0x1111111111111111111111111111111111111111", 1),
        ("0x2222222222222222222222222222222222222222", 2),
    ]
    a1 = MerkleAirdrop.from_entries(entries)
    a2 = MerkleAirdrop.from_entries(list(reversed(entries)))
    assert a1.root == a2.root
