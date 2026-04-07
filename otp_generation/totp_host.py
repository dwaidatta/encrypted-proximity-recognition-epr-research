import os
import time
import hmac
import hashlib
from dotenv import load_dotenv

load_dotenv()
T_VALID = int(os.getenv("T_VALID", 120))  # seconds, default 2 min
OTP_LENGTH = 6

def generate_otp(host_key: str) -> str:
    epoch = int(time.time()) // T_VALID
    msg = epoch.to_bytes(8, "big")
    raw = hmac.new(host_key.encode(), msg, hashlib.sha256).digest()
    offset = raw[-1] & 0x0F
    code = int.from_bytes(raw[offset:offset+4], "big") & 0x7FFFFFFF
    return str(code % (10 ** OTP_LENGTH)).zfill(OTP_LENGTH)

def verify_otp(host_key: str, submitted_otp: str) -> bool:
    return generate_otp(host_key) == submitted_otp

if __name__ == "__main__":
    host_key = "your_host_long_term_key_here"
    otp = generate_otp(host_key)
    print(f"Current OTP: {otp}")
    print(f"Valid: {verify_otp(host_key, otp)}")
