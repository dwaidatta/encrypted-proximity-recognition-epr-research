# /mixing_function/avalanche_test.py

import os
import sys
import json
import hashlib
import requests
import time
from dotenv import load_dotenv

load_dotenv()
API_URL = "https://api.quantumnumbers.anu.edu.au"
API_KEY = os.getenv("ANU_API_KEY")
HEADERS = {"x-api-key": API_KEY}
ALPHANUM = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
QKEY_LENGTH = 8


# ── Mixing function with fixed theta (for deterministic testing) ─────────────

def _cyclic_xor(a: bytes, b: bytes) -> bytes:
    return bytes(a[i] ^ b[i % len(b)] for i in range(len(a)))

def _temper(data: bytes) -> bytes:
    result = bytearray(data)
    for i in range(len(result)):
        result[i] = ((result[i] << 3) | (result[i] >> 5)) & 0xFF
        result[i] ^= (result[i] >> 2)
    return bytes(result)

def generate_qkey_fixed(user_key: str, qotp: str, user_id: str, theta: bytes) -> str:
    """Same as generate_qkey but accepts theta as parameter instead of calling QRNG."""
    k_bytes  = user_key.encode()
    q_bytes  = qotp.encode()
    xored    = _cyclic_xor(k_bytes, q_bytes)
    tempered = _temper(xored)
    payload  = tempered + user_id.encode() + theta
    digest   = hashlib.sha256(payload).digest()
    s        = int(user_id.encode().hex(), 16) % 10
    selected = digest[s:s + QKEY_LENGTH]
    return "".join(ALPHANUM[b % len(ALPHANUM)] for b in selected)


# ── QRNG fetch for test inputs ───────────────────────────────────────────────

def fetch_qrng_uint8(n_requests=10, length=1024):
    data = []
    for i in range(n_requests):
        try:
            r = requests.get(API_URL, headers=HEADERS,
                             params={"length": length, "type": "uint8"}, timeout=10)
            data.extend(r.json()["data"])
            time.sleep(0.1)
        except Exception as e:
            print(f"  Request {i+1} failed: {e}")
    return data


# ── Test utilities ───────────────────────────────────────────────────────────

def to_bits(value: str) -> list:
    return [int(b) for byte in value.encode() for b in format(byte, '08b')]

def flip_bit_in_string(s: str, bit_pos: int) -> str:
    b = bytearray(s.encode())
    byte_idx = bit_pos // 8
    bit_idx  = 7 - (bit_pos % 8)
    if byte_idx < len(b):
        b[byte_idx] ^= (1 << bit_idx)
    return b.decode(errors='replace')


# ── Avalanche test ───────────────────────────────────────────────────────────

def avalanche_test(raw_bytes, n_samples=500):
    """
    For each sample, fix theta and flip one bit at a time in user_key.
    Measure average percentage of output bits that change.
    Ideal: ~50%
    """
    print(f"\nRunning avalanche test on {n_samples} samples...")
    change_ratios = []
    fixed_theta = bytes(raw_bytes[:16])  # one fixed theta for all runs

    for i in range(n_samples):
        offset   = (i * 50) % (len(raw_bytes) - 40)
        user_key = bytes(raw_bytes[offset:offset+32]).hex()[:32]
        qotp     = bytes(raw_bytes[offset+32:offset+40]).hex()[:8]
        user_id  = f"USER_{i:04d}"

        original = generate_qkey_fixed(user_key, qotp, user_id, fixed_theta)
        orig_bits = to_bits(original)
        n_out     = len(orig_bits)

        bit_changes = []
        for bit_pos in range(min(len(user_key) * 8, 64)):
            flipped     = flip_bit_in_string(user_key, bit_pos)
            flipped_out = generate_qkey_fixed(flipped, qotp, user_id, fixed_theta)
            dist        = sum(a != b for a, b in zip(orig_bits, to_bits(flipped_out)))
            bit_changes.append(dist / n_out)

        change_ratios.append(sum(bit_changes) / len(bit_changes))

    avg = sum(change_ratios) / len(change_ratios)
    return {
        "average_bit_change_pct": round(avg * 100, 4),
        "min_pct":  round(min(change_ratios) * 100, 4),
        "max_pct":  round(max(change_ratios) * 100, 4),
        "ideal_pct": 50.0
    }


# ── Collision test ───────────────────────────────────────────────────────────

def collision_test(raw_bytes, n_samples=1000):
    """Generate n_samples QKeys from distinct inputs, count collisions."""
    print(f"Running collision test on {n_samples} samples...")
    seen       = set()
    collisions = 0
    fixed_theta = bytes(raw_bytes[:16])

    for i in range(n_samples):
        offset   = (i * 50) % (len(raw_bytes) - 40)
        user_key = bytes(raw_bytes[offset:offset+32]).hex()[:32]
        qotp     = bytes(raw_bytes[offset+32:offset+40]).hex()[:8]
        user_id  = f"USER_{i:04d}"

        qkey = generate_qkey_fixed(user_key, qotp, user_id, fixed_theta)
        if qkey in seen:
            collisions += 1
        seen.add(qkey)

    return {
        "samples_tested":   n_samples,
        "collisions_found": collisions,
        "collision_rate":   round(collisions / n_samples, 6)
    }


# ── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    N_REQUESTS = 10   # 10 requests = $0.05, gives 10240 bytes — sufficient
    print(f"Fetching test inputs from ANU QRNG ({N_REQUESTS} requests)...")
    raw_bytes = fetch_qrng_uint8(N_REQUESTS, length=1024)
    print(f"Total bytes fetched: {len(raw_bytes)}")

    avalanche = avalanche_test(raw_bytes, n_samples=500)
    collision = collision_test(raw_bytes, n_samples=1000)

    print("\n── Avalanche Effect ──")
    for k, v in avalanche.items():
        print(f"  {k}: {v}")

    print("\n── Collision Resistance ──")
    for k, v in collision.items():
        print(f"  {k}: {v}")

    results = {"avalanche": avalanche, "collision": collision}
    with open("mixing_function_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print("\nResults saved to mixing_function_results.json")