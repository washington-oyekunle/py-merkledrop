"""Example: build an airdrop and print proofs."""

from merkledrop import HashAlgo, MerkleAirdrop


def main() -> None:
    entries = [
        ("0xAb5801a7D398351b8bE11C439e05C5B3259aeC9B", 10_000 * 10**18),
        ("0x742d35Cc6634C0532925a3b844Bc454e4438f44e", 5_000 * 10**18),
        ("0x5aAeb6053F3E94C9b9A09f33669435E7Ef1BeAed", 1_000 * 10**18),
        ("0xfB6916095ca1df60bB79Ce92cE3Ea74c37c5d359", 500 * 10**18),
    ]

    print("=== SHA-256 ===")
    a = MerkleAirdrop.from_entries(entries, algo=HashAlgo.SHA256)
    print(a.stats())
    proof = a.get_proof(entries[0][0])
    print("Proof length:", len(proof))
    assert a.verify(entries[0][0], entries[0][1], proof)

    print("\n=== Keccak-256 (Ethereum) ===")
    b = MerkleAirdrop.from_entries(entries, algo=HashAlgo.KECCAK256)
    print(b.stats())
    proof = b.get_proof(entries[0][0])
    assert b.verify(entries[0][0], entries[0][1], proof)
    print("Verification: SUCCESS")


if __name__ == "__main__":
    main()
