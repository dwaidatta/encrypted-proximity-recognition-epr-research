import os
import requests
from dotenv import load_dotenv

load_dotenv()
API_URL = "https://api.quantumnumbers.anu.edu.au"
API_KEY = os.getenv("ANU_API_KEY")
HEADERS = {"x-api-key": API_KEY}

def get_uint8(length=10):
    r = requests.get(API_URL, headers=HEADERS, params={"length": length, "type": "uint8"})
    return r.json()["data"]

def get_uint16(length=5):
    r = requests.get(API_URL, headers=HEADERS, params={"length": length, "type": "uint16"})
    return r.json()["data"]

def get_hex8(length=10, size=1):
    r = requests.get(API_URL, headers=HEADERS, params={"length": length, "type": "hex8", "size": size})
    return r.json()["data"]

def get_hex16(length=10, size=2):
    r = requests.get(API_URL, headers=HEADERS, params={"length": length, "type": "hex16", "size": size})
    return r.json()["data"]

if __name__ == "__main__":
    print("uint8 :", get_uint8(5))
    print("uint16:", get_uint16(5))
    print("hex8  :", get_hex8(5, size=1))
    print("hex16 :", get_hex16(5, size=2))
