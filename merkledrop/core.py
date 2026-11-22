"""
Core Merkle airdrop engine.
Supports SHA-256 and Ethereum-compatible Keccak-256.
"""

from __future__ import annotations

import csv
import hashlib
import json
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple, Union

from .keccak import keccak256


class HashAlgo(str, Enum):
    SHA256 = "sha256"
    KECCAK256 = "keccak256"  # Ethereum-compatible


def _hash(data: bytes, algo: HashAlgo) -> bytes:
    if algo == HashAlgo.SHA256:
        return hashlib.sha256(data).digest()
    if algo == HashAlgo.KECCAK256:
        return keccak256(data)
    raise ValueError(f"Unsupported hash algorithm: {algo}")


def _normalize_address(address: str) -> str:
    addr = address.strip().lower()
    if addr.startswith("0x"):
        addr = addr[2:]
    if len(addr) != 40 or any(c not in "0123456789abcdef" for c in addr):
        raise ValueError(f"Invalid Ethereum address: {address}")
    return addr


def hash_leaf(address: str, amount: int, algo: HashAlgo = HashAlgo.SHA256) -> bytes:
    """
    Leaf = hash(address_bytes || amount_uint256_be)
    Matches common Solidity pattern: hash(abi.encodePacked(account, amount))
    when using the same hash function.
    """
    addr = _normalize_address(address)
    addr_bytes = bytes.fromhex(addr)
    amount_bytes = int(amount).to_bytes(32, "big")
    return _hash(addr_bytes + amount_bytes, algo)


class MerkleAirdrop:
    """
    Deterministic sorted-pair Merkle tree for token airdrops.

    - Leaves are sorted for canonical roots regardless of input order.
    - Odd nodes are duplicated (standard approach).
    - Supports SHA-256 (default) and Ethereum Keccak-256.
    """

    def __init__(
        self,
        entries: Sequence[Tuple[str, int]],
        algo: HashAlgo = HashAlgo.SHA256,
    ):
        if not entries:
            raise ValueError("At least one entry is required")

        self.algo = algo
        self.entries: List[Tuple[str, int]] = [
            (_normalize_address(addr), int(amt)) for addr, amt in entries
        ]
        # Deduplicate by address (last amount wins) while preserving determinism
        seen: Dict[str, int] = {}
        for addr, amt in self.entries:
            seen[addr] = amt
        self.entries = sorted(seen.items())  # sorted by address

        self.leaves = [hash_leaf(addr, amt, algo) for addr, amt in self.entries]
        self._leaf_to_index = {leaf: i for i, leaf in enumerate(self.leaves)}
        self.root = self._build_root(self.leaves)

    @classmethod
    def from_entries(
        cls,
        entries: Sequence[Tuple[str, int]],
        algo: HashAlgo = HashAlgo.SHA256,
    ) -> "MerkleAirdrop":
        return cls(entries, algo=algo)

    @classmethod
    def from_csv(
        cls,
        path: Union[str, Path],
        algo: HashAlgo = HashAlgo.SHA256,
        address_col: str = "address",
        amount_col: str = "amount",
    ) -> "MerkleAirdrop":
        entries: List[Tuple[str, int]] = []
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            if not reader.fieldnames or address_col not in reader.fieldnames or amount_col not in reader.fieldnames:
                raise ValueError(f"CSV must contain columns '{address_col}' and '{amount_col}'")
            for row in reader:
                addr = row[address_col].strip()
                if not addr:
                    continue
                amt = int(float(row[amount_col]))  # allow "1000.0"
                entries.append((addr, amt))
        return cls(entries, algo=algo)

    def _build_root(self, nodes: List[bytes]) -> bytes:
        if len(nodes) == 1:
            return nodes[0]
        next_level: List[bytes] = []
        for i in range(0, len(nodes), 2):
            left = nodes[i]
            right = nodes[i + 1] if i + 1 < len(nodes) else left
            if left > right:
                left, right = right, left
            next_level.append(_hash(left + right, self.algo))
        return self._build_root(next_level)

    @property
    def root_hex(self) -> str:
        return "0x" + self.root.hex()

    @property
    def size(self) -> int:
        return len(self.entries)

    def get_proof(self, address: str, amount: Optional[int] = None) -> List[str]:
        """
        Return sibling hashes (hex) for the given address.
        If amount is omitted, looks up the amount stored for that address.
        """
        addr = _normalize_address(address)
        if amount is None:
            for a, amt in self.entries:
                if a == addr:
                    amount = amt
                    break
            if amount is None:
                raise ValueError(f"Address not found in airdrop: {address}")
        else:
            amount = int(amount)

        leaf = hash_leaf(addr, amount, self.algo)
        if leaf not in self._leaf_to_index:
            raise ValueError(f"Leaf not found for {address} with amount {amount}")

        index = self._leaf_to_index[leaf]
        current = list(self.leaves)
        proof: List[str] = []

        while len(current) > 1:
            sibling_idx = index ^ 1
            if sibling_idx < len(current):
                proof.append("0x" + current[sibling_idx].hex())
            # Build next level
            next_level: List[bytes] = []
            for i in range(0, len(current), 2):
                left = current[i]
                right = current[i + 1] if i + 1 < len(current) else left
                if left > right:
                    left, right = right, left
                next_level.append(_hash(left + right, self.algo))
            current = next_level
            index //= 2

        return proof

    def verify(self, address: str, amount: int, proof: Sequence[str]) -> bool:
        """Verify a Merkle proof against this tree's root."""
        leaf = hash_leaf(address, amount, self.algo)
        computed = leaf
        for p in proof:
            sibling = bytes.fromhex(p.removeprefix("0x"))
            if computed > sibling:
                computed, sibling = sibling, computed
            computed = _hash(computed + sibling, self.algo)
        return computed == self.root

    def export_proofs(self) -> Dict[str, dict]:
        """Export all proofs keyed by lowercase address (with 0x)."""
        result: Dict[str, dict] = {}
        for addr, amt in self.entries:
            proof = self.get_proof(addr, amt)
            result["0x" + addr] = {
                "amount": amt,
                "proof": proof,
                "leaf": "0x" + hash_leaf(addr, amt, self.algo).hex(),
            }
        return result

    def save_proofs(self, path: Union[str, Path]) -> None:
        data = {
            "root": self.root_hex,
            "algo": self.algo.value,
            "count": self.size,
            "proofs": self.export_proofs(),
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def stats(self) -> dict:
        amounts = [amt for _, amt in self.entries]
        return {
            "recipients": self.size,
            "total_amount": sum(amounts),
            "min_amount": min(amounts),
            "max_amount": max(amounts),
            "root": self.root_hex,
            "algo": self.algo.value,
        }


def generate_from_csv(
    csv_path: Union[str, Path],
    output_dir: Union[str, Path] = ".",
    algo: HashAlgo = HashAlgo.SHA256,
) -> str:
    """Load CSV, build tree, write root + proofs, return root hex."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    airdrop = MerkleAirdrop.from_csv(csv_path, algo=algo)
    (output_dir / "merkle_root.txt").write_text(airdrop.root_hex + "\n", encoding="utf-8")
    airdrop.save_proofs(output_dir / "proofs.json")
    return airdrop.root_hex
