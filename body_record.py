# modules/body_record.py
import sqlite3
from datetime import datetime
from contextlib import contextmanager
from linebot.models import TextSendMessage, TemplateSendMessage, ButtonsTemplate, FlexSendMessage

PAGE_SIZE = 10

@contextmanager
def get_db_connection(database):
    conn = sqlite3.connect(database)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def show_body_record_menu(event, line_bot_api):
    flex_message = FlexSendMessage(
        alt_text="體態紀錄選單",
        contents={
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",
                "contents": [
                    {"type": "text", "text": "📊 體態紀錄", "weight": "bold", "size": "xl"},
                    {"type": "text", "text": "請選擇您要進行的操作：", "size": "sm", "color": "#555555"}
                ]
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",
                "contents": [
                    {
                        "type": "button",
                        "style": "primary",
                        "action": {"type": "message", "label": "✍️ 輸入紀錄", "text": "輸入紀錄"}
                    },
                    {
                        "type": "button",
                        "style": "primary",
                        "action": {"type": "message", "label": "📚 查詢紀錄", "text": "查詢紀錄"}
                    }
                ]
            }
        }
    )
    line_bot_api.reply_message(event.reply_token, flex_message)

def prompt_body_record_input(event, line_bot_api):
    flex_message = TextSendMessage(
        text=(
            "✍️ 請輸入您的體重和身高，例如：\n"
            "格式：體重（公斤） 身高（公分）。\n"
            "傳送「取消」退出。"
        )
    )
    line_bot_api.reply_message(event.reply_token, flex_message)

def initialize_db(database):
    with get_db_connection(database) as conn:
        c = conn.cursor()
        # 建立資料表，如果尚未存在
        c.execute('''
            CREATE TABLE IF NOT EXISTS body_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                weight REAL NOT NULL,
                height REAL NOT NULL,
                bmi REAL NOT NULL,
                time TEXT NOT NULL
            )
        ''')
        conn.commit()

def insert_body_data(database, user_id, weight, height, bmi, current_time):
    with get_db_connection(database) as conn:
        c = conn.cursor()
        c.execute('''INSERT INTO body_data (user_id, weight, height, bmi, time)
                     VALUES (?, ?, ?, ?, ?)''', 
                  (user_id, weight, height, bmi, current_time))
        conn.commit()

def handle_body_record_input(event, line_bot_api, database, weight, height):
    user_id = event.source.user_id
    height_m = height / 100
    bmi = weight / (height_m ** 2)
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        # 初始化資料庫和資料表
        initialize_db(database)

        # 插入資料
        insert_body_data(database, user_id, weight, height, bmi, current_time)

        # 回覆用戶訊息
        reply_message = (
            f"✅ 體態紀錄成功！\n"
            f"📅 記錄時間：{current_time}\n"
            f"⚖️ 體重：{weight} kg\n"
            f"📏 身高：{height} cm\n"
            f"📊 BMI：{bmi:.2f}"
        )
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply_message)
        )
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="❌ 體態紀錄失敗，請稍後再試。")
        )

# 範例主程式
if __name__ == "__main__":
    # 假設有以下參數
    class MockEvent:
        class Source:
            user_id = "U1234567890"
        source = Source()
        reply_token = "dummy_token"

    class MockLineBotAPI:
        def reply_message(self, reply_token, messages):
            print(f"Reply sent to {reply_token}: {messages}")

    event = MockEvent()
    line_bot_api = MockLineBotAPI()
    database = r'D:\User\Downloads\test.io\test.io\user_body_data.db'
    weight = 70.5  # 體重（公斤）
    height = 175.0  # 身高（公分）

    handle_body_record_input(event, line_bot_api, database, weight, height)

def show_body_records(event, line_bot_api, database, page=1, user_states=None):
    user_id = event.source.user_id
    offset = (page - 1) * PAGE_SIZE
    with get_db_connection(database) as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM body_data WHERE user_id = ? ORDER BY time DESC LIMIT ? OFFSET ?", (user_id, PAGE_SIZE, offset))
        records = c.fetchall()
        c.execute("SELECT COUNT(*) FROM body_data WHERE user_id = ?", (user_id,))
        total_records = c.fetchone()[0]

    if not records:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="📋 您尚無任何體態紀錄。"))
        return

    reply_message = "📋 您的體態紀錄：\n\n"
    for idx, record in enumerate(records, start=offset + 1):
        reply_message += (
            f"• 第 {idx} 條紀錄：\n"
            f"  ⏰ 時間: {record['time']} \n"
            f"  ⚖️ 體重: {record['weight']} kg\n"
            f"  📏 身高: {record['height']} cm\n"
            f"  📊 BMI: {record['bmi']:.2f}\n\n"
        )

    total_pages = (total_records + PAGE_SIZE - 1) // PAGE_SIZE

    # 建立分頁按鈕
    actions = []
    if page > 1:
        actions.append({"type": "message", "label": "⬅️ 上一頁", "text": "體態紀錄上一頁"})
    if page < total_pages:
        actions.append({"type": "message", "label": "下一頁 ➡️", "text": "體態紀錄下一頁"})

    # 若提供了 user_states，將使用者狀態設定為瀏覽紀錄狀態
    if user_states is not None:
        user_states[user_id] = {'state': 'viewing_body_records', 'page': page}

    if actions:
        buttons_template = TemplateSendMessage(
            alt_text="體態紀錄導航",
            template=ButtonsTemplate(
                text=f"第 {page} 頁，共 {total_pages} 頁",
                actions=actions
            )
        )
        line_bot_api.reply_message(event.reply_token, [TextSendMessage(text=reply_message), buttons_template])
    else:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_message))

def handle_body_record_pagination(event, direction, line_bot_api, user_states, database):
    user_id = event.source.user_id
    if user_id not in user_states:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="❌ 無法找到您的紀錄狀態。"))
        return

    state = user_states[user_id]
    if state.get('state') != 'viewing_body_records':
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="❌ 您目前沒有瀏覽紀錄。"))
        return

    current_page = state.get('page', 1)
    if direction == "上一頁" and current_page > 1:
        new_page = current_page - 1
    elif direction == "下一頁":
        new_page = current_page + 1
    else:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="❌ 沒有更多的頁面。"))
        return

    # 顯示新頁的紀錄
    show_body_records(event, line_bot_api, database, page=new_page, user_states=user_states)
