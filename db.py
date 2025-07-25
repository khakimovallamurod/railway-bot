from tinydb import TinyDB, Query
from tinydb.table import Document
import hashlib
from datetime import datetime
import re

class RailwayDB:
    def __init__(self):
        self.db = TinyDB('railway_data.json', indent=4)
        self.table = self.db.table("Railway_DB")
        self.query = Query()
        self.adminfile = 'admin_chatIDs.txt'
    
    def data_insert(self, data):
        if data.get('route') != None:
            route_key = ''.join([word[0] for word in data['route']]).lower()
            raw_id = f"{data['chat_id']}_{data['signal_text']}_{data['date']}_{route_key}"
            doc_id = self.generate_doc_id(raw_id)
            data_one = Document(data, doc_id=doc_id)
            if self.check_data(doc_id):
                self.table.insert(data_one)
            else:
                self.table.update(data_one, doc_ids=[doc_id])
            return True
        return False
    
    def generate_doc_id(self, doc_id):
        
        hash_str = hashlib.md5(doc_id.encode()).hexdigest()
        int_hash = int(hash_str, 16)
        octal_hash = int(oct(int_hash)[2:])  # 8-likka o‘tkazamiz (string oldidan "0o" olib tashlaymiz)
        return octal_hash
    
    def get_signal_data(self, doc_id):
        doc_id = self.generate_doc_id(doc_id)
        signal_data = self.table.get(doc_id=doc_id)
        return signal_data
        
    def update_signal(self, doc_id):
        doc_id = int(self.generate_doc_id(doc_id))
        if self.table.get(doc_id=doc_id) != None:
            res = self.table.update({'active': False}, doc_ids=[doc_id])
            return True
        else :
            return False
    
    def delete_signal(self, doc_id):
        
        doc_id = int(self.generate_doc_id(doc_id))

        if self.table.get(doc_id=doc_id) != None:
            x = self.table.remove(doc_ids=[doc_id])
            return True
        else:
            return False
    
    def check_data(self, doc_id):
        if self.table.get(doc_id=doc_id) == None:
            return True
        return False
    
    def get_actives(self):

        active_data = self.table.search(self.query.active == True)
        return active_data
    
    def add_admin(self, chat_id):
        chat_id = str(chat_id)
        get_ids = self.get_admin_chatIDs()

        with open(self.adminfile, 'a') as file:
            if chat_id.isdigit() and len(chat_id) in list(range(9, 15)) and chat_id not in get_ids:
                file.write(chat_id+"\n")
                file.close()
                return True
            else:
                return False

    def get_admin_chatIDs(self):
        with open(self.adminfile, 'r') as file:
            chat_ids = file.read().split('\n')
        return chat_ids

    def check_date(self, sana_str: str):
        kun, oy, yil = map(int, sana_str.split("-"))
        if 1 <= kun <= 31 and 1 <= oy <= 12:
            try_sana = datetime(yil, oy, kun)
            return try_sana.date() <= datetime.now().date()
        return False
    
    def is_valid_date(self, date: str) -> bool:
        """Sanani YYYY-MM-DD formatida tekshiradi."""
        pattern = r"^\d{4}-\d{2}-\d{2}$"
        if not re.match(pattern, date):
            return False
        try:
            datetime.strptime(date, "%Y-%m-%d")
            return True
        except ValueError:
            return False