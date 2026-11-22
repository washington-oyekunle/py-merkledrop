"""
py-merkledrop: Pure Python Merkle tree airdrop toolkit.
Zero external dependencies. Deterministic, sorted-pair Merkle trees.
"""

from __future__ import annotations

import csv
import hashlib
import json
from typing import Dict, List, Optional, Tuple


def _hash(data: bytes) -> bytes:
    """SHA-256 hash. Compatible with many on-chain implementations (adjust to keccak if needed)."""
    return hashlib.sha256(data).digest()


def _hash_leaf(address: str, amount: int) -> bytes:
    """Create leaf: hash(address_bytes + amount_bytes)."""
    # Normalize address
    addr = address.lower().removeprefix("0x")
    if len(addr) != 40:
        raise ValueError(f"Invalid address length: {address}")
    addr_bytes = bytes.fromhex(addr)
    amount_bytes = amount.to_bytes(32, "big")
    return _hash(addr_bytes + amount_bytes)


class MerkleNode:
    def __init__(self, data: bytes, left: Optional["MerkleNode"] = None, right: Optional["MerkleNode"] = None):
        self.data = data
        self.left = left
        self.right = right

    @property
    def is_leaf(self) -> bool:
        return self.left is None and self.right is None


class MerkleAirdrop:
    """Merkle tree for token airdrops. Sorted pairs for deterministic roots."""

    def __init__(self, leaves: List[bytes]):
        if not leaves:
            raise ValueError("At least one leaf required")
        self.leaves = sorted(leaves)  # Sort for determinism
        self.tree = self._build_tree(self.leaves)
        self.root = self.tree.data
        self._leaf_map: Dict[bytes, int] = {leaf: i for i, leaf in enumerate(self.leaves)}

    @classmethod
    def from_entries(cls, entries: List[Tuple[str, int]]) -> "MerkleAirdrop":
        leaves = [_hash_leaf(addr, amt) for addr, amt in entries]
        return cls(leaves)

    @classmethod
    def from_csv(cls, path: str) -> "MerkleAirdrop":
        entries = []
        with open(path, newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                addr = row["address"].strip()
                amt = int(row["amount"])
                entries.append((addr, amt))
        return cls.from_entries(entries)

    def _build_tree(self, nodes: List[bytes]) -> MerkleNode:
        if len(nodes) == 1:
            return MerkleNode(nodes[0])

        # Pair up, hash sorted pairs
        next_level = []
        for i in range(0, len(nodes), 2):
            left = nodes[i]
            right = nodes[i + 1] if i + 1 < len(nodes) else left  # Duplicate last if odd
            # Sort pair for canonical order
            if left > right:
                left, right = right, left
            combined = _hash(left + right)
            next_level.append(combined)

        return self._build_tree(next_level)

    @property
    def root_hex(self) -> str:
        return "0x" + self.root.hex()

    def get_proof(self, address: str, amount: int) -> List[str]:
        """Return list of sibling hashes (hex) needed to prove inclusion."""
        leaf = _hash_leaf(address, amount)
        if leaf not in self._leaf_map:
            raise ValueError("Address/amount not in airdrop")

        # Rebuild levels to collect proof (simple but clear)
        current_level = self.leaves[:]
        index = self._leaf_map[leaf]
        proof = []

        while len(current_level) > 1:
            sibling_index = index ^ 1  # XOR with 1 flips last bit
            if sibling_index < len(current_level):
                sibling = current_level[sibling_index]
                proof.append("0x" + sibling.hex())
            # Move to next level
            next_level = []
            for i in range(0, len(current_level), 2):
                left = current_level[i]
                right = current_level[i + 1] if i + 1 < len(current_level) else left
                if left > right:
                    left, right = right, left
                next_level.append(_hash(left + right))
            current_level = next_level
            index //= 2

        return proof

    def verify(self, address: str, amount: int, proof: List[str]) -> bool:
        """Verify a proof against the stored root."""
        leaf = _hash_leaf(address, amount)
        computed = leaf
        for p in proof:
            sibling = bytes.fromhex(p.removeprefix("0x"))
            # Sort to match construction
            if computed > sibling:
                computed, sibling = sibling, computed
            computed = _hash(computed + sibling)
        return computed == self.root

    def export_proofs(self, entries: List[Tuple[str, int]]) -> Dict[str, dict]:
        """Export all proofs as JSON-serializable dict keyed by address."""
        result = {}
        for addr, amt in entries:
            try:
                proof = self.get_proof(addr, amt)
                result[addr.lower()] = {
                    "amount": amt,
                    "proof": proof,
                    "leaf": "0x" + _hash_leaf(addr, amt).hex(),
                }
            except ValueError:
                continue
        return result

    def save_proofs(self, path: str, entries: List[Tuple[str, int]]) -> None:
        data = {
            "root": self.root_hex,
            "proofs": self.export_proofs(entries),
        }
        with open(path, "w") as f:
            json.dump(data, f, indent=2)


def generate_from_csv(csv_path: str, output_dir: str = ".") -> str:
    """Convenience: load CSV, build tree, save root and proofs."""
    airdrop = MerkleAirdrop.from_csv(csv_path)
    # Reload entries for export
    entries = []
    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            entries.append((row["address"].strip(), int(row["amount"])))

    root_path = f"{output_dir}/merkle_root.txt"
    proofs_path = f"{output_dir}/proofs.json"
    with open(root_path, "w") as f:
        f.write(airdrop.root_hex)
    airdrop.save_proofs(proofs_path, entries)
    return airdrop.root_hex
