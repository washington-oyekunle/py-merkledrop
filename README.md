# py-merkledrop

**Pure Python Merkle tree airdrop toolkit** with Ethereum-compatible Keccak-256.

Generate roots, proofs, and verify claims for any token airdrop. **Zero runtime dependencies.**

![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Zero Deps](https://img.shields.io/badge/dependencies-none-brightgreen.svg)
![Version](https://img.shields.io/badge/version-0.2.0-orange.svg)

## Why this exists

On-chain airdrops that store every recipient cost too much gas.  
Store only a **Merkle root**. Users prove inclusion with a short proof.

This library produces those roots and proofs offline, then pairs cleanly with a minimal Solidity claim contract.

## Features (v0.2)

- Deterministic sorted-pair Merkle trees
- **SHA-256** and **Ethereum Keccak-256** (pure Python implementation)
- CSV → root + proofs in one command
- CLI: `generate`, `proof`, `verify`, `stats`
- Production-oriented Solidity claim contract (sorted pairs + IERC20)
- Full test suite
- Package structure (`pip install -e .`)

## Quick start

```bash
git clone https://github.com/washington-oyekunle/py-merkledrop.git
cd py-merkledrop
python -m pip install -e ".[dev]"
```

### 1. Prepare recipients

```csv
address,amount
0x1111111111111111111111111111111111111111,1000000000000000000
0x2222222222222222222222222222222222222222,500000000000000000
```

### 2. Generate (Ethereum style)

```bash
python cli.py --algo keccak256 generate airdrop.csv -o ./out
```

Outputs:
- `out/merkle_root.txt`
- `out/proofs.json`

### 3. Get a single proof

```bash
python cli.py --algo keccak256 proof airdrop.csv 0x1111...1111
```

### 4. Verify

```bash
python cli.py --algo keccak256 verify <root> <address> <amount> '["0x...", "0x..."]'
```

## Library usage

```python
from merkledrop import MerkleAirdrop, HashAlgo

entries = [
    ("0x1111111111111111111111111111111111111111", 10**18),
    ("0x2222222222222222222222222222222222222222", 5 * 10**17),
]

airdrop = MerkleAirdrop.from_entries(entries, algo=HashAlgo.KECCAK256)
print(airdrop.root_hex)
print(airdrop.stats())

proof = airdrop.get_proof("0x1111111111111111111111111111111111111111")
assert airdrop.verify("0x1111111111111111111111111111111111111111", 10**18, proof)
```

## On-chain

See `contracts/MerkleAirdrop.sol`.

Leaf construction (must match the Python side):

```solidity
bytes32 leaf = keccak256(abi.encodePacked(account, amount));
```

Tree nodes are hashed after sorting the pair so the root is independent of insertion order.

## Hash algorithms

| Flag | Algorithm | Notes |
|------|-----------|-------|
| `--algo sha256` (default) | SHA-256 | Fast, widely available |
| `--algo keccak256` | Ethereum Keccak-256 | Pure Python, matches Solidity `keccak256` |

## Roadmap

- [x] Core sorted Merkle tree
- [x] SHA-256 + pure Keccak-256
- [x] CLI + stats
- [x] Solidity claim contract
- [x] Package + tests
- [ ] Batch claim helper
- [ ] Simple HTML claim page example
- [ ] Benchmarks for 100k recipients

## License

MIT
