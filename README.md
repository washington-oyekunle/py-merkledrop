# py-merkledrop

**Pure Python Merkle tree airdrop toolkit.**

Generate Merkle roots, proofs, and verify claims for any token airdrop. Zero external dependencies. Production-ready for real-world campaigns.

Perfect for token launches, community rewards, and on-chain claim systems.

![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Zero Deps](https://img.shields.io/badge/dependencies-none-brightgreen.svg)

## Why py-merkledrop?

- **Real-world usable**: Used by projects to distribute tokens fairly without storing every address on-chain.
- **Gas efficient**: Only the Merkle root is stored on-chain. Users submit proofs to claim.
- **Privacy & fairness**: Supports large lists (10k+ addresses) efficiently.
- **Auditable**: Pure Python, fully deterministic, sorted pairs for canonical trees.
- **CLI + Library**: Use as library or command-line tool.
- **Includes Solidity template**: Ready-to-deploy claim contract.

## Quick Start

```bash
git clone https://github.com/washington-oyekunle/py-merkledrop.git
cd py-merkledrop
python -m pip install -e .  # optional, or just run files
```

### Generate airdrop from CSV

Create `airdrop.csv`:
```csv
address,amount
0x1111111111111111111111111111111111111111,1000
0x2222222222222222222222222222222222222222,500
```

```bash
python cli.py generate airdrop.csv
```

Outputs `merkle_root.txt` and `proofs.json`.

### Generate proof for an address

```bash
python cli.py proof airdrop.csv 0x1111...1111
```

### Verify a proof

```bash
python cli.py verify <root> <address> <amount> <proof_json>
```

## Library Usage

```python
from merkledrop import MerkleAirdrop

airdrop = MerkleAirdrop.from_csv("airdrop.csv")
print(airdrop.root)

proof = airdrop.get_proof("0x1111...")
assert airdrop.verify("0x1111...", 1000, proof)
```

## On-chain Integration

See `contracts/MerkleAirdrop.sol` for a minimal claim contract that stores the root and verifies proofs.

## Architecture

- Leaves: `keccak256(abi.encodePacked(address, amount))` compatible style (or pure SHA256)
- Sorted pairs: Ensures deterministic root regardless of insertion order
- Double hashing: Standard Merkle construction

## Roadmap

- [x] Core Merkle tree (sorted)
- [x] CSV loader + CLI
- [x] Proof generation & verification
- [x] Solidity template
- [ ] Batch proof optimization
- [ ] EIP-712 typed data support
- [ ] Frontend claim UI example

## License

MIT
