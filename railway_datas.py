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
        self.url = config.get_url()
    
    def railway_response_data(self):
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
                    "depDate": self.date,
                    "fullday": True,
                    "type": "Forward"
                }
            ],
            "stationFrom": self.stationFrom,
            "stationTo": self.stationTo,
            "detailNumPlaces": 1,
            "showWithoutPlaces": 0
        }
        try:
            response = requests.post(self.url, headers=headers, cookies=cookies, json=data)
            res_data = response.json()
            data_res = json.dumps(res_data, indent=4)
            with open('data_json.json', 'w') as file:
                file.write(data_res)
            return res_data
        except:
            return None
    def get_need_data(self, type):
        select_type = self.check_class_name(type=type)
        if select_type == None:
            return "notclass", None
        
        datas = self.railway_response_data()
        print(datas)
        try:
            freeSeats_text = []
            total_free_seats = 0
            passRoute = datas['express']['direction'][0]['passRoute']
            route = [passRoute['from'], passRoute['to']]
            for train in datas['express']['direction'][0]['trains']:
                    for t in train['train']:
                        if t['brand'] in ["Afrosiyob", "Sharq"]:
                            total_free_seats_one = 0
                            total_free_seats_all = 0
                            for car in t["places"]["cars"]:
                                for tar in car["tariffs"]["tariff"]:
                                    
                                    if tar["classService"]["type"] == select_type:
                                        seats_undef = tar["seats"]["seatsUndef"]
                                        if seats_undef is not None:
                                            total_free_seats_one += int(tar["seats"]["seatsUndef"])
                                total_free_seats_all += int(car['freeSeats'])
                            if select_type == "all":
                                freeSeats_text.append(
                                    [
                                        t['number'], t['brand'], t['departure']['localTime'], t['arrival']['localTime'], total_free_seats_all, route
                                    ]
                                )
                                
                                total_free_seats += total_free_seats_all
                            else:
                                freeSeats_text.append(
                                    [
                                        t['number'], t['brand'], t['departure']['localTime'], t['arrival']['localTime'], total_free_seats_one, route
                                    ]
                                )
                                total_free_seats += total_free_seats_one
            print(freeSeats_text)
            return freeSeats_text, total_free_seats
        except:
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

    def is_valid_date(self):
        pattern = r"^\d{2}\.\d{2}\.\d{4}$"
        if not re.match(pattern, self.date):
            return False  

        try:
            datetime.strptime(self.date, "%d.%m.%Y")
            return True  
        except ValueError:
            return False 
    
    
obj = Railway(stationFrom="2900920", stationTo="2900790", date='24.4.2025')
print(obj.railway_response_data())