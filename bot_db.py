import sqlite3
import time


class Database:
    def __init__(self, db_file):
        '''ПОдключаемся к бд '''
        self.connection = sqlite3.connect(db_file)
        self.cursor = self.connection.cursor()

    def update_fields(self):
        ''' check fields '''
        try:
            with self.connection:
                # add last_active_time column
                self.cursor.execute("ALTER TABLE users ADD COLUMN last_active_time INTEGER DEFAULT 0")
            return True
        except Exception as ex:
            print(ex)
            return False

    async def user_exists(self, user_id:int) -> bool:
        with self.connection:
            result = self.cursor.execute("SELECT user_id FROM users WHERE user_id=?", (user_id, ))
            return result.fetchone() is not None

    async def referral_exists(self, user_id:int) -> bool:
        with self.connection:
            result = self.cursor.execute("SELECT id FROM users WHERE user_id=? AND referral_id IS NOT NULL AND referral_id != ''", (user_id, ))
            return result.fetchone() is not None

    def get_referral_id(self, user_id:int):
        with self.connection:
            result = self.cursor.execute("SELECT referral_id FROM users WHERE referral_id IS NOT NULL AND referral_id != '' AND user_id=?", (user_id, )).fetchone()
            if result != None:
                return result[0]
            return result

    def get_user_id(self, user_id:int):
        with self.connection:
            result = self.cursor.execute("SELECT * FROM users WHERE user_id=? AND referral_id IS NOT NULL AND referral_id != ''", (user_id, ))
            return result.fetchone() is not None

    def add_user(self, user_id:int, referral_id=None, name_user:str='') -> None:
        reg_date = int(time.time())
        with self.connection:
            self.cursor.execute("INSERT INTO users (user_id, referral_id, name_user, date_sub, reg_date, last_active_time) VALUES (?, ?, ?, ?, ?, ?)", (user_id, referral_id, name_user, reg_date, reg_date, reg_date))

    def count_referral(self, user_id:int) -> int:
        with self.connection:
            result = self.cursor.execute("SELECT COUNT(id) as count FROM users WHERE referral_id=?", (user_id, )).fetchone()
            if result != None:
                return result[0]
            return result

    def get_date(self, user_id:int):
        with self.connection:
            result = self.cursor.execute("SELECT date_sub FROM users WHERE user_id=?", (user_id, )).fetchone()
            if result != None:
                return result[0]
            return result

    def get_referral_discount(self, user_id:int) -> bool:
        with self.connection:
            result = self.cursor.execute("SELECT status FROM users WHERE user_id=? AND referral_id IS NOT NULL AND referral_id != '' AND status != 1", (user_id,)).fetchone()
            if result != None:
                # if true to false and false to true
                return True
            return False

    async def set_first_pay_status(self, user_id:int) -> None:
        with self.connection:
            self.cursor.execute("UPDATE users SET status=1 WHERE user_id=?", (user_id, ))


    def add_date_sub(self, user_id:int, date_sub:int) -> None:
        old_date = self.get_date(user_id)
        if old_date == None:
            old_date = time.time()
        if old_date < int(time.time()):
            old_date = time.time()
        date_sub_int = int(old_date) + date_sub *24 *60 *60
        with self.connection:
            self.cursor.execute("UPDATE users SET date_sub=? WHERE user_id=?", (date_sub_int, user_id, ))

    def add_date_sub_status(self, user_id:int, date_sub:int, status:int) -> None:
        old_date = self.get_date(user_id)
        if old_date == None:
            old_date = time.time()
        if old_date < int(time.time()):
            old_date = time.time()
        date_sub_int = int(old_date) + date_sub *24 *60 *60
        with self.connection:
            self.cursor.execute("UPDATE users SET date_sub=?, status=1 WHERE user_id=?", (date_sub_int, user_id, ))

    async def set_last_active_time(self, user_id:int) -> None:
        last_active = int(time.time())
        with self.connection:
            self.cursor.execute("UPDATE users SET last_active_time=? WHERE user_id=?", (last_active, user_id,))

    def get_users_reminder_days(self, days:int):
        last_active = int(time.time()) - days *24 *60 *60
        with self.connection:
            result = self.cursor.execute("SELECT user_id FROM users WHERE last_active_time>0 AND last_active_time<?", (last_active, )).fetchall()
            if result != None:
                return result
            return None;

    def get_date_status(self, user_id:int) -> bool:
        with self.connection:
            result = self.cursor.execute("SELECT date_sub FROM users WHERE user_id=?", (user_id, )).fetchone()
            if result == None:
                time_from = time.time()
            else:
                time_from = result[0]

            return int(time_from) > int(time.time())
    
    async def increment_counter_msg(self, user_id:int) -> None:
        with self.connection:
            self.cursor.execute("UPDATE users SET count_message=count_message+1 WHERE user_id=?", (user_id, ))
    
    def get_counter_msg(self, user_id:int) -> int:
        with self.connection:
            result = self.cursor.execute("SELECT count_message FROM users WHERE user_id=?", (user_id, )).fetchone()
            if result != None:
                return result[0]
            return result

    def add_payment(self, user_id:int, payment_id:str, status:str, summ:str, payload: str) -> None:
        reg_date = int(time.time())
        with self.connection:
            self.cursor.execute("INSERT INTO payments (user_id, payment_id, status, summ, date_create, payload) VALUES (?, ?, ?, ?, ?, ?)", (user_id, payment_id, status, summ, reg_date, payload,))

    def get_payments_for_status(self, status:str):
        with self.connection:
            result = self.cursor.execute("SELECT payment_id, user_id, payload FROM payments WHERE status=?", (status, )).fetchall()
            if result != None:
                return result
            return None;

    def update_payment_status(self, payment_id:str, status:str) -> None:
        reg_date = int(time.time())
        with self.connection:
            self.cursor.execute("UPDATE payments SET status=?, date_oper=? WHERE payment_id=?", (status, reg_date, payment_id, ))
 