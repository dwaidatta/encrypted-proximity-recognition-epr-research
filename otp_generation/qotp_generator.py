import os
import requests
from dotenv import load_dotenv

load_dotenv()
API_URL = "https://api.quantumnumbers.anu.edu.au"
API_KEY = os.getenv("ANU_API_KEY")
HEADERS = {"x-api-key": API_KEY}
ALPHANUM = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
QOTP_LENGTH = 8

def generate_qotp() -> str:
    r = requests.get(API_URL, headers=HEADERS, params={"length": QOTP_LENGTH, "type": "uint8"})
    indices = r.json()["data"]
    return "".join(ALPHANUM[i % len(ALPHANUM)] for i in indices)

if __name__ == "__main__":
    qotp = generate_qotp()
    print(f"QOtp: {qotp}")
