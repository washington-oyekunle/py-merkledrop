"""
py-merkledrop: Pure Python Merkle tree airdrop toolkit.
Zero external dependencies. Deterministic sorted-pair Merkle trees.
"""

from .core import MerkleAirdrop, generate_from_csv, HashAlgo
from .keccak import keccak256

__version__ = "0.2.0"
__all__ = ["MerkleAirdrop", "generate_from_csv", "HashAlgo", "keccak256"]
