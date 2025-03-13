from tinydb import TinyDB, Query
from tinydb.table import Document
import hashlib


class RailwayDB:
    def __init__(self):
        self.db = TinyDB('railway_data.json', indent=4)
        self.table = self.db.table("Railway_DB")
        self.query = Query()
    
    def data_insert(self, data):
        raw_id = f"{data['chat_id']}_{data['signal_text']}_{data['date']}"
        doc_id = self.generate_doc_id(raw_id)
        
        if self.check_data(doc_id):
            data_one = Document(data, doc_id=doc_id)
            self.table.insert(data_one)
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
        res = self.table.update({'active': False}, doc_ids=[doc_id])

        return res
    
    def check_data(self, doc_id):
        
        if self.table.get(doc_id=doc_id) == None:
            return True
        return False
    
    def get_actives(self):

        active_data = self.table.search(self.query.active == True)
        return active_data
