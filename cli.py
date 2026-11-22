#!/usr/bin/env python3
"""CLI for py-merkledrop."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from merkledrop import HashAlgo, MerkleAirdrop, generate_from_csv


def _parse_algo(value: str) -> HashAlgo:
    value = value.lower().strip()
    if value in ("sha256", "sha-256"):
        return HashAlgo.SHA256
    if value in ("keccak256", "keccak", "keccak-256"):
        return HashAlgo.KECCAK256
    raise argparse.ArgumentTypeError(f"Unknown algo: {value}. Use sha256 or keccak256")


def cmd_generate(args: argparse.Namespace) -> None:
    root = generate_from_csv(args.csv, args.output, algo=args.algo)
    airdrop = MerkleAirdrop.from_csv(args.csv, algo=args.algo)
    stats = airdrop.stats()
    print(f"Merkle root ({args.algo.value}): {root}")
    print(f"Recipients : {stats['recipients']}")
    print(f"Total amount: {stats['total_amount']}")
    print(f"Wrote {args.output}/merkle_root.txt and {args.output}/proofs.json")


def cmd_proof(args: argparse.Namespace) -> None:
    airdrop = MerkleAirdrop.from_csv(args.csv, algo=args.algo)
    proof = airdrop.get_proof(args.address, args.amount)
    # Resolve amount for display
    amount = args.amount
    if amount is None:
        for a, amt in airdrop.entries:
            if a == args.address.lower().removeprefix("0x"):
                amount = amt
                break
    result = {
        "root": airdrop.root_hex,
        "algo": airdrop.algo.value,
        "address": args.address,
        "amount": amount,
        "proof": proof,
    }
    print(json.dumps(result, indent=2))


def cmd_verify(args: argparse.Namespace) -> None:
    if args.proof.startswith("[") or args.proof.startswith("{"):
        proof_data = json.loads(args.proof)
    else:
        proof_data = json.loads(Path(args.proof).read_text(encoding="utf-8"))

    if isinstance(proof_data, dict):
        proof = proof_data.get("proof", proof_data)
    else:
        proof = proof_data

    from merkledrop.core import hash_leaf, _hash

    leaf = hash_leaf(args.address, args.amount, args.algo)
    computed = leaf
    for p in proof:
        sibling = bytes.fromhex(p.removeprefix("0x"))
        if computed > sibling:
            computed, sibling = sibling, computed
        computed = _hash(computed + sibling, args.algo)

    expected = bytes.fromhex(args.root.removeprefix("0x"))
    if computed == expected:
        print("VALID proof")
        sys.exit(0)
    else:
        print("INVALID proof")
        sys.exit(1)


def cmd_stats(args: argparse.Namespace) -> None:
    airdrop = MerkleAirdrop.from_csv(args.csv, algo=args.algo)
    stats = airdrop.stats()
    print(json.dumps(stats, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="py-merkledrop — pure Python Merkle airdrop toolkit",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--algo",
        type=_parse_algo,
        default=HashAlgo.SHA256,
        help="Hash algorithm: sha256 (default) or keccak256 (Ethereum)",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    p_gen = sub.add_parser("generate", help="Build root + proofs from CSV")
    p_gen.add_argument("csv", help="CSV with address,amount columns")
    p_gen.add_argument("-o", "--output", default=".", help="Output directory")
    p_gen.set_defaults(func=cmd_generate)

    p_proof = sub.add_parser("proof", help="Get proof for one address")
    p_proof.add_argument("csv")
    p_proof.add_argument("address")
    p_proof.add_argument("--amount", type=int, default=None, help="Optional; looked up if omitted")
    p_proof.set_defaults(func=cmd_proof)

    p_ver = sub.add_parser("verify", help="Verify a proof against a root")
    p_ver.add_argument("root")
    p_ver.add_argument("address")
    p_ver.add_argument("amount", type=int)
    p_ver.add_argument("proof", help="JSON array or path to proofs file / proof array")
    p_ver.set_defaults(func=cmd_verify)

    p_stats = sub.add_parser("stats", help="Show airdrop statistics")
    p_stats.add_argument("csv")
    p_stats.set_defaults(func=cmd_stats)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
