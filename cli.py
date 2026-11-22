#!/usr/bin/env python3
"""CLI for py-merkledrop."""

import argparse
import json
import sys
from pathlib import Path

from merkledrop import MerkleAirdrop, generate_from_csv


def cmd_generate(args):
    root = generate_from_csv(args.csv, args.output)
    print(f"Merkle root: {root}")
    print(f"Saved to {args.output}/merkle_root.txt and {args.output}/proofs.json")


def cmd_proof(args):
    airdrop = MerkleAirdrop.from_csv(args.csv)
    # Find amount
    amount = None
    with open(args.csv, newline="") as f:
        import csv
        reader = csv.DictReader(f)
        for row in reader:
            if row["address"].strip().lower() == args.address.lower():
                amount = int(row["amount"])
                break
    if amount is None:
        print("Address not found in CSV", file=sys.stderr)
        sys.exit(1)

    proof = airdrop.get_proof(args.address, amount)
    result = {
        "root": airdrop.root_hex,
        "address": args.address,
        "amount": amount,
        "proof": proof,
    }
    print(json.dumps(result, indent=2))


def cmd_verify(args):
    proof = json.loads(args.proof) if args.proof.startswith("[") else json.loads(Path(args.proof).read_text())
    if isinstance(proof, dict):
        proof = proof.get("proof", proof)

    # Reconstruct minimal for verify
    from merkledrop import _hash_leaf, _hash
    computed = _hash_leaf(args.address, args.amount)
    for p in proof:
        sibling = bytes.fromhex(p.removeprefix("0x"))
        if computed > sibling:
            computed, sibling = sibling, computed
        computed = _hash(computed + sibling)

    expected = bytes.fromhex(args.root.removeprefix("0x"))
    if computed == expected:
        print("VALID proof")
        sys.exit(0)
    else:
        print("INVALID proof")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="py-merkledrop CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    p_gen = sub.add_parser("generate", help="Generate root and proofs from CSV")
    p_gen.add_argument("csv")
    p_gen.add_argument("--output", "-o", default=".")
    p_gen.set_defaults(func=cmd_generate)

    p_proof = sub.add_parser("proof", help="Get proof for an address")
    p_proof.add_argument("csv")
    p_proof.add_argument("address")
    p_proof.set_defaults(func=cmd_proof)

    p_ver = sub.add_parser("verify", help="Verify a proof")
    p_ver.add_argument("root")
    p_ver.add_argument("address")
    p_ver.add_argument("amount", type=int)
    p_ver.add_argument("proof", help="JSON array or path to file")
    p_ver.set_defaults(func=cmd_verify)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
