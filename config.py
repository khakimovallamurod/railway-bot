from dotenv import load_dotenv
import os

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

def get_access_token():
    ACCESS_TOKEN = os.getenv("access_token")
    if ACCESS_TOKEN is None:
        raise ValueError("ACCESS_TOKEN not found.")
    return ACCESS_TOKEN
def get_xsrf_token():
    XSRF_TOKEN = os.getenv("xsrf_token")
    if XSRF_TOKEN is None:
        raise ValueError("XSRF_TOKEN not found.")
    return XSRF_TOKEN