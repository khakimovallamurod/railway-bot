import requests
import config
import re
from datetime import datetime

def reilway_counts(date):
    url = config.get_url()
    cookies = {
        "_ga": "GA1.1.1017869759.1741497848",
        "__stripe_mid": "5de3b064-7296-45f7-9f07-c2d0af097a48f714af",
        "__stripe_sid": "09f86a30-f148-451e-a804-8a3217ee2d790a78a9",
        "_ga_K4H2SZ7MWK": "GS1.1.1741497848.1.1.1741501222.0.0.0",
        "SL_G_WPT_TO": "en",
        "XSRF-TOKEN": "8900ba92-e3d2-43e5-b9c9-0ffe3647cc13",
        "G_ENABLED_IDPS": "google"
    }

    headers = {
        "Accept": "application/json",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "uz",
        "Authorization": "Bearer eyJhbGciOiJIUzM4NCJ9.eyJyb2xlIjoiVVNFUiIsImlkIjoiZmFmZTJhZjQtYmNhNS00MGQ5LWJkMjAtZjIxY2M4NzJjZDNmIiwic3ViIjoiOTk4OTM4NTU0NjQwIiwiaWF0IjoxNzQxNTAxMzI2LCJleHAiOjE3NDE1MDQ5MjZ9.cWwif1eVbnG9-ii9j6WFXPY7f3C0QAjMldvaxGtaf1tW16FQozsl0t_qi0cyJQ0f",
        "Connection": "keep-alive",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
        "X-XSRF-TOKEN": "8900ba92-e3d2-43e5-b9c9-0ffe3647cc13",
        "Device-Type": "BROWSER",
        "Origin": "https://eticket.railway.uz",
        "Referer": "https://eticket.railway.uz/uz/home",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin"
    }
    data = {
        "direction": [
            {
                "depDate": date,
                "fullday": True,
                "type": "Forward"
            }
        ],
        "stationFrom": "2900700",
        "stationTo": "2900000",
        "detailNumPlaces": 1,
        "showWithoutPlaces": 0
    }
    response = requests.post(url, headers=headers, cookies=cookies, json=data)
    res_data = response.json()
    freeSeats = sum(
            int(car['freeSeats'])
            for direction in res_data.get('express', {}).get('direction', [])
            for train in direction.get('trains', [])
            for t in train.get('train', [])
            for car in t.get('places', {}).get('cars', [])
        )
    return freeSeats


def is_valid_date(date_str):
    
    pattern = r"^\d{2}\.\d{2}\.\d{4}$"
    if not re.match(pattern, date_str):
        return False  

    try:
        datetime.strptime(date_str, "%d.%m.%Y")
        return True  
    except ValueError:
        return False  


