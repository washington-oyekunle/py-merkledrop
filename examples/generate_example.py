"""Example usage of py-merkledrop."""

from merkledrop import MerkleAirdrop

def main():
    entries = [
        ("0xAb5801a7D398351b8bE11C439e05C5B3259aeC9B", 10_000 * 10**18),  # Vitalik-style
        ("0x742d35Cc6634C0532925a3b844Bc454e4438f44e", 5_000 * 10**18),
        ("0x5aAeb6053F3E94C9b9A09f33669435E7Ef1BeAed", 1_000 * 10**18),
        ("0xfB6916095ca1df60bB79Ce92cE3Ea74c37c5d359", 500 * 10**18),
    ]

    airdrop = MerkleAirdrop.from_entries(entries)
    print(f"Root: {airdrop.root_hex}")
    print(f"Number of recipients: {len(entries)}")

    # Generate proof for first address
    addr, amt = entries[0]
    proof = airdrop.get_proof(addr, amt)
    print(f"\nProof for {addr[:10]}...:")
    for i, p in enumerate(proof):
        print(f"  [{i}] {p}")

    assert airdrop.verify(addr, amt, proof)
    print("\nVerification: SUCCESS")

    # Export all
    proofs = airdrop.export_proofs(entries)
    print(f"\nExported {len(proofs)} proofs")

if __name__ == "__main__":
    main()
