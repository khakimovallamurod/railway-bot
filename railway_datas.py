import requests
import config
import re
from datetime import datetime
import json

class Railway:
    def __init__(self, stationFrom, stationTo, date):
        self.stationFrom = stationFrom
        self.stationTo = stationTo
        self.date = date
        self.url =  config.get_url() 
        
    
    def railway_response_data(self):
        headers = {
            "accept": "application/json",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "uz",
            "authorization": f"Bearer {config.get_access_token()}",
            "connection": "keep-alive",
            "content-type": "application/json",
            "cookie": f"_ga=GA1.1.952475370.1751366484; G_ENABLED_IDPS=google; XSRF-TOKEN={config.get_xsrf_token()}; __stripe_sid=5059f297-b706-425d-8ec6-45c9e5e608729678de",
            "device-type": "BROWSER",
            "origin": "https://eticket.railway.uz",
            "referer": "https://eticket.railway.uz/uz/pages/trains-page",
            "sec-ch-ua": "\"Chromium\";v=\"137\", \"Not/A)Brand\";v=\"24\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Linux\"",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
            "x-xsrf-token": config.get_xsrf_token()
        }
        payload = {
            "directions": {
                "forward": {
                    "date": self.date,
                    "depStationCode": self.stationFrom,
                    "arvStationCode": self.stationTo
                }
            }
        }
        response = requests.post(self.url, headers=headers, json=payload)
        res_data = response.json()
        return res_data

    def get_need_data(self, type):
        select_type = self.check_class_name(type=type)
        if select_type is None:
            return "notclass", None
        try:
            datas = self.railway_response_data()
            freeSeats_text = []
            total_free_seats = 0

            direction = datas["data"]["directions"]["forward"]
            for train in direction["trains"]:
                brand = train.get("brand", "").encode().decode('utf-8')

                if brand not in ["Afrosiyob", "Sharq", "Пассажирский"]:
                    continue

                total_free_seats_one = 0
                total_free_seats_all = 0

                for car in train["cars"]:
                    car_free_seats = car.get("freeSeats", 0)
                    total_free_seats_all += car_free_seats

                    for tariff in car.get("tariffs", []):
                        class_type = tariff.get("classServiceType")
                        if select_type == "all" or class_type == select_type:
                            total_free_seats_one += tariff.get("freeSeats", 0)

                sub_route = train.get("subRoute", {})
                route = [sub_route.get("depStationName"), sub_route.get("arvStationName")]

                if select_type == "all":
                    freeSeats_text.append([
                        train["number"],
                        brand,
                        train["departureDate"],
                        train["arrivalDate"],
                        total_free_seats_all,
                        route
                    ])
                    total_free_seats += total_free_seats_all
                else:
                    freeSeats_text.append([
                        train["number"],
                        brand,
                        train["departureDate"],
                        train["arrivalDate"],
                        total_free_seats_one,
                        route
                    ])
                    total_free_seats += total_free_seats_one

            return freeSeats_text, total_free_seats
        except Exception as e:
            print(f"[ERROR] Railway data fetching error: {e}")
            return None, None
    
    def check_class_name(self, type):
        class_names = {
            "Econom": "2\u0415",
            "Biznes": "1\u0421",
            "VIP": "1\u0412",
            "Kupe": "2\u041a",
            "Platskart": "3\u041f",
            "Sidячий": "2\u0412",
            "ALL": 'all'
        }
        return class_names.get(type)

