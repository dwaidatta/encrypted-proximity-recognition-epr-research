import os
import hashlib
import requests
from dotenv import load_dotenv

load_dotenv()
API_URL = "https://api.quantumnumbers.anu.edu.au"
API_KEY = os.getenv("ANU_API_KEY")
HEADERS = {"x-api-key": API_KEY}
SALT = os.getenv("SYSTEM_SALT", "epr-framework-salt")

def _qrng_hex(length=10, size=8):
    r = requests.get(API_URL, headers=HEADERS, params={"length": length, "type": "hex16", "size": size})
    return "".join(r.json()["data"])

def generate_long_term_key(entity_id: str) -> str:
    quantum_seed = _qrng_hex(length=10, size=8)
    raw = f"{entity_id}{SALT}{quantum_seed}"
    key = hashlib.sha256(raw.encode()).hexdigest()
    return key

if __name__ == "__main__":
    user_id = "USER_001"
    host_id = "HOST_A1"
    user_key = generate_long_term_key(user_id)
    host_key = generate_long_term_key(host_id)
    print(f"User {user_id} Key: {user_key}")
    print(f"Host {host_id} Key: {host_key}")
