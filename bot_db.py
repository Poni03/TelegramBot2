import sqlite3
import time


class Database:
    def __init__(self, db_file):
        '''ПОдключаемся к бд '''
        self.connection = sqlite3.connect(db_file)
        self.cursor = self.connection.cursor()

    async def user_exists(self, user_id:int) -> bool:
        with self.connection:
            result = self.cursor.execute("SELECT user_id FROM users WHERE user_id=?", (user_id, ))
            return result.fetchone() is not None

    async def referral_exists(self, user_id:int) -> bool:
        with self.connection:
            result = self.cursor.execute("SELECT id FROM users WHERE user_id=? AND referral_id IS NOT NULL", (user_id, ))
            return result.fetchone() is not None

    def get_referral_id(self, user_id:int):
        with self.connection:
            result = self.cursor.execute("SELECT referral_id FROM users WHERE user_id=?", (user_id, )).fetchone()
            if result != None:
                return result[0]
            return result

    def add_user(self, user_id:int, referral_id=None, name_user:str='') -> None:
        reg_date = int(time.time())
        with self.connection:
            self.cursor.execute("INSERT INTO users (user_id, referral_id, name_user, date_sub, reg_date) VALUES (?, ?, ?, ?, ?)", (user_id, referral_id, name_user, reg_date, reg_date))

    def count_referral(self, user_id:int) -> int:
        with self.connection:
            result = self.cursor.execute("SELECT COUNT(id) as count FROM users WHERE referral_id=?", (user_id, )).fetchone()
            if result != None:
                return result[0]
            return result

    def get_date(self, user_id:int):
        with self.connection:
            result = self.cursor.execute(f"SELECT date_sub FROM users WHERE user_id={user_id}").fetchone()
            if result != None:
                return result[0]
            return result

    def add_date_sub(self, user_id:int, date_sub:int) -> None:
        old_date = self.get_date(user_id)
        if old_date == None:
            old_date = time.time()
        date_sub_int = int(old_date) + date_sub *24 *60 *60
        with self.connection:
            self.cursor.execute(f"UPDATE users SET date_sub={date_sub_int} WHERE user_id={user_id}")	
	
    def get_date_status(self, user_id:int) -> bool:
        with self.connection:
            result = self.cursor.execute(f"SELECT date_sub FROM users WHERE user_id={user_id}").fetchone()
            if result == None:
                time_from = time.time()
            else:
                time_from = result[0]

            return int(time_from) > int(time.time())
    
    async def increment_counter_msg(self, user_id:int) -> None:
        with self.connection:
            self.cursor.execute(f"UPDATE users SET count_message=count_message+1 WHERE user_id={user_id}")
    
    def get_counter_msg(self, user_id:int) -> int:
        with self.connection:
            result = self.cursor.execute(f"SELECT count_message FROM users WHERE user_id={user_id}").fetchone()
            if result != None:
                return result[0]
            return result
