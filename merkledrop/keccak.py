"""
Minimal pure-Python Keccak-256 implementation.
Matches Ethereum's keccak256 (pre-NIST SHA-3 padding).
No external dependencies.
"""

from __future__ import annotations

# Round constants
_RC = [
    0x0000000000000001, 0x0000000000008082, 0x800000000000808A,
    0x8000000080008000, 0x000000000000808B, 0x0000000080000001,
    0x8000000080008081, 0x8000000000008009, 0x000000000000008A,
    0x0000000000000088, 0x0000000080008009, 0x000000008000000A,
    0x000000008000808B, 0x800000000000008B, 0x8000000000008089,
    0x8000000000008003, 0x8000000000008002, 0x8000000000000080,
    0x000000000000800A, 0x800000008000000A, 0x8000000080008081,
    0x8000000000008080, 0x0000000080000001, 0x8000000080008008,
]

_ROT = [
    [0, 36, 3, 41, 18],
    [1, 44, 10, 45, 2],
    [62, 6, 43, 15, 61],
    [28, 55, 25, 21, 56],
    [27, 20, 39, 8, 14],
]


def _rotl64(x: int, n: int) -> int:
    return ((x << n) | (x >> (64 - n))) & 0xFFFFFFFFFFFFFFFF


def _keccak_f(state: list[int]) -> None:
    for round_idx in range(24):
        # Theta
        C = [state[x] ^ state[x + 5] ^ state[x + 10] ^ state[x + 15] ^ state[x + 20] for x in range(5)]
        D = [C[(x - 1) % 5] ^ _rotl64(C[(x + 1) % 5], 1) for x in range(5)]
        for x in range(5):
            for y in range(5):
                state[x + 5 * y] ^= D[x]

        # Rho + Pi
        B = [0] * 25
        for x in range(5):
            for y in range(5):
                B[y + 5 * ((2 * x + 3 * y) % 5)] = _rotl64(state[x + 5 * y], _ROT[x][y])

        # Chi
        for y in range(5):
            for x in range(5):
                state[x + 5 * y] = B[x + 5 * y] ^ ((~B[((x + 1) % 5) + 5 * y]) & B[((x + 2) % 5) + 5 * y])

        # Iota
        state[0] ^= _RC[round_idx]


def keccak256(data: bytes) -> bytes:
    """Compute Keccak-256 (Ethereum-compatible)."""
    rate = 136  # 1088 bits for Keccak-256
    state = [0] * 25
    # Absorb
    offset = 0
    while offset < len(data):
        block = data[offset : offset + rate]
        for i in range(0, len(block), 8):
            lane = int.from_bytes(block[i : i + 8].ljust(8, b"\x00"), "little")
            state[i // 8] ^= lane
        if len(block) == rate:
            _keccak_f(state)
            offset += rate
        else:
            break
    else:
        block = b""

    # Padding (Keccak multi-rate padding: 0x01 ... 0x80)
    pad_len = rate - len(block)
    padded = bytearray(block)
    padded.append(0x01)
    padded.extend(b"\x00" * (pad_len - 2))
    padded.append(0x80)

    for i in range(0, rate, 8):
        lane = int.from_bytes(padded[i : i + 8], "little")
        state[i // 8] ^= lane
    _keccak_f(state)

    # Squeeze 32 bytes
    out = bytearray()
    for i in range(4):
        out.extend(state[i].to_bytes(8, "little"))
    return bytes(out)
