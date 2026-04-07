import os
import hashlib
import requests
from dotenv import load_dotenv

load_dotenv()
API_URL = "https://api.quantumnumbers.anu.edu.au"
API_KEY = os.getenv("ANU_API_KEY")
HEADERS = {"x-api-key": API_KEY}
ALPHANUM = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
QKEY_LENGTH = 8

def _qrng_uint8(length=16):
    r = requests.get(API_URL, headers=HEADERS, params={"length": length, "type": "uint8"})
    return bytes(r.json()["data"])

def _cyclic_xor(a: bytes, b: bytes) -> bytes:
    return bytes(a[i] ^ b[i % len(b)] for i in range(len(a)))

def _temper(data: bytes) -> bytes:
    result = bytearray(data)
    for i in range(len(result)):
        result[i] = ((result[i] << 3) | (result[i] >> 5)) & 0xFF
        result[i] ^= (result[i] >> 2)
    return bytes(result)

def generate_qkey(user_key: str, qotp: str, user_id: str) -> str:
    theta = _qrng_uint8(16)
    k_bytes = user_key.encode()
    q_bytes = qotp.encode()
    xored = _cyclic_xor(k_bytes, q_bytes)
    tempered = _temper(xored)
    payload = tempered + user_id.encode() + theta
    digest = hashlib.sha256(payload).digest()
    s = int(user_id.encode().hex(), 16) % 10
    selected = digest[s:s + QKEY_LENGTH]
    return "".join(ALPHANUM[b % len(ALPHANUM)] for b in selected)

if __name__ == "__main__":
    user_key = "your_user_long_term_key_here"
    qotp = "AbCd1234"
    user_id = "USER_001"
    qkey = generate_qkey(user_key, qotp, user_id)
    print(f"QKey: {qkey}")
