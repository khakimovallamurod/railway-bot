import os
from dotenv import load_dotenv
import json

def read_json():
    with open("token_data.json", "r") as f:
        return json.load(f)
    
load_dotenv()

def get_token():
    TOKEN = os.getenv("token")
    if TOKEN is None:
        raise ValueError("TOKEN not found.")
    return TOKEN

def get_url():
    URL = os.getenv("url")
    if URL is None:
        raise ValueError("URL not found.")
    return URL

def get_phone():
    PHONE = os.getenv("phone")
    if PHONE is None:
        raise ValueError("PHONE not found.")
    return PHONE

def get_password():
    PASSWORD = os.getenv("password")
    if PASSWORD is None:
        raise ValueError("PASSWORD not found.")
    return PASSWORD

def get_access_token():
    data = read_json()
    return data["access_token"]

def get_xsrf_token():
    data = read_json()
    return data["xsrf_token"]