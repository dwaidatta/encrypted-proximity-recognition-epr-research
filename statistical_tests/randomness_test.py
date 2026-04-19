# /statistical_tests/randomness_test.py
# Tests: Frequency, Entropy, Serial Correlation, Runs Test
# Compares QRNG (ANU), CSPRNG (os.urandom), PRNG (random module)
# Budget: ~100 API requests (1024 uint8 each = 102400 bytes of quantum data)

import os
import math
import random
import requests
import time
from dotenv import load_dotenv

load_dotenv()
API_URL = "https://api.quantumnumbers.anu.edu.au"
API_KEY = os.getenv("ANU_API_KEY")
HEADERS = {"x-api-key": API_KEY}

# ── Data Collection ──────────────────────────────────────────────────────────

def fetch_qrng_bytes(n_requests=100, length=1024):
    """Fetch quantum random bytes. n_requests * length = total bytes."""
    data = []
    for i in range(n_requests):
        try:
            r = requests.get(API_URL, headers=HEADERS,
                             params={"length": length, "type": "uint8"}, timeout=10)
            data.extend(r.json()["data"])
            time.sleep(0.1)  # gentle rate limiting
            if (i + 1) % 10 == 0:
                print(f"  Fetched {(i+1)*length} bytes...")
        except Exception as e:
            print(f"  Request {i+1} failed: {e}")
    return bytes(data)

def get_csprng_bytes(n_bytes):
    return os.urandom(n_bytes)

def get_prng_bytes(n_bytes, seed=42):
    rng = random.Random(seed)
    return bytes([rng.randint(0, 255) for _ in range(n_bytes)])

# ── Statistical Tests ────────────────────────────────────────────────────────

def bytes_to_bits(data: bytes) -> list:
    bits = []
    for byte in data:
        for i in range(7, -1, -1):
            bits.append((byte >> i) & 1)
    return bits

def frequency_test(data: bytes) -> dict:
    """Proportion of 1s in bit stream. Ideal: 0.5"""
    bits = bytes_to_bits(data)
    ones = sum(bits)
    proportion = ones / len(bits)
    deviation = abs(proportion - 0.5)
    return {"ones_proportion": round(proportion, 6), "deviation_from_ideal": round(deviation, 6)}

def entropy_test(data: bytes) -> dict:
    """Shannon entropy per byte. Ideal: 8.0 bits"""
    freq = [0] * 256
    for b in data:
        freq[b] += 1
    n = len(data)
    entropy = -sum((f/n) * math.log2(f/n) for f in freq if f > 0)
    return {"shannon_entropy_bits": round(entropy, 6)}

def serial_correlation_test(data: bytes) -> dict:
    """Correlation between consecutive bytes. Ideal: ~0.0"""
    n = len(data)
    mean = sum(data) / n
    numerator = sum((data[i] - mean) * (data[i+1] - mean) for i in range(n-1))
    denominator = sum((b - mean) ** 2 for b in data)
    correlation = numerator / denominator if denominator != 0 else 0
    return {"serial_correlation": round(correlation, 6)}

def runs_test(data: bytes) -> dict:
    """
    Count runs (consecutive identical bits). 
    Ratio of runs to total bits. Ideal: ~0.5
    A run is a maximal sequence of identical bits.
    """
    bits = bytes_to_bits(data)
    runs = 1
    for i in range(1, len(bits)):
        if bits[i] != bits[i-1]:
            runs += 1
    ratio = runs / len(bits)
    return {"runs_ratio": round(ratio, 6)}

# ── Main ─────────────────────────────────────────────────────────────────────

def run_all_tests(label: str, data: bytes) -> dict:
    print(f"\nRunning tests on {label} ({len(data)} bytes)...")
    results = {"source": label, "bytes_tested": len(data)}
    results.update(frequency_test(data))
    results.update(entropy_test(data))
    results.update(serial_correlation_test(data))
    results.update(runs_test(data))
    return results

def print_table(results_list):
    metrics = ["ones_proportion", "deviation_from_ideal",
               "shannon_entropy_bits", "serial_correlation", "runs_ratio"]
    ideal =   [0.5,               0.0,                    8.0,                  0.0,                 0.5]

    col_w = 20
    header = f"{'Metric':<30}" + "".join(f"{r['source']:>{col_w}}" for r in results_list)
    print("\n" + "=" * (30 + col_w * len(results_list)))
    print(header)
    print("=" * (30 + col_w * len(results_list)))
    for metric, ideal_val in zip(metrics, ideal):
        row = f"{metric:<30}"
        for r in results_list:
            row += f"{r[metric]:>{col_w}}"
        row += f"   (ideal: {ideal_val})"
        print(row)
    print("=" * (30 + col_w * len(results_list)))

if __name__ == "__main__":
    N_REQUESTS = 100      # $0.50 — 102,400 bytes of quantum data
    LENGTH     = 1024

    print(f"Fetching {N_REQUESTS * LENGTH:,} bytes from ANU QRNG ({N_REQUESTS} requests)...")
    qrng_data = fetch_qrng_bytes(N_REQUESTS, LENGTH)

    n_bytes = len(qrng_data)
    csprng_data = get_csprng_bytes(n_bytes)
    prng_data   = get_prng_bytes(n_bytes)

    results = [
        run_all_tests("QRNG (ANU)", qrng_data),
        run_all_tests("CSPRNG (os.urandom)", csprng_data),
        run_all_tests("PRNG (random)", prng_data),
    ]

    print_table(results)

    # Save raw results for paper
    import json
    with open("randomness_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print("\nResults saved to randomness_test_results.json")