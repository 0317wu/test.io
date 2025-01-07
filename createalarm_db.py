# createalarm_db.py

import sqlite3

CREATEALARM_DB = 'createalarm.db'

def create_reminders_table():
    conn = sqlite3.connect(CREATEALARM_DB)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            reminder_time TEXT NOT NULL,  -- 使用 ISO 格式的日期時間字符串
            message TEXT,
            frequency TEXT DEFAULT NULL  -- 新增頻率欄位，用於重複提醒
        );
    ''')
    conn.commit()
    conn.close()
    print("已成功建立 `reminders` 表格於 `createalarm.db`。")

if __name__ == "__main__":
    create_reminders_table()
