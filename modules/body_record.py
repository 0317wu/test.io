# modules/body_record.py
import os
import sqlite3
from datetime import datetime
from contextlib import contextmanager
from linebot.models import (
    TextSendMessage, TemplateSendMessage, ButtonsTemplate, 
    FlexSendMessage, ImageSendMessage
)
import matplotlib.pyplot as plt
import uuid

# 確保 img 目錄存在
if not os.path.exists('img'):
    os.makedirs('img')

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
                    },
                    {
                        "type": "button",
                        "style": "primary",
                        "action": {"type": "message", "label": "📈 顯示體重圖表", "text": "顯示體重圖表"}
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

    messages = [TextSendMessage(text=reply_message)]
    
    if actions:
        buttons_template = TemplateSendMessage(
            alt_text="體態紀錄導航",
            template=ButtonsTemplate(
                text=f"第 {page} 頁，共 {total_pages} 頁",
                actions=actions
            )
        )
        messages.append(buttons_template)

    # 發送體重變化圖表
    try:
        image_url = generate_weight_and_bmi_charts(user_id, database)
        image_message = ImageSendMessage(
            original_content_url=image_url,
            preview_image_url=image_url
        )
        messages.append(image_message)
    except Exception as e:
        print(f"Chart generation error: {e}")
        messages.append(TextSendMessage(text="⚠️ 體重變化圖表生成失敗。"))

    line_bot_api.reply_message(event.reply_token, messages)

def generate_weight_and_bmi_charts(user_id, database, num_records=10):
    print("開始生成體重和BMI變化圖表...")
    with get_db_connection(database) as conn:
        c = conn.cursor()
        # 取得最近的 num_records 條紀錄，按時間升序排列
        c.execute("SELECT time, weight, bmi FROM body_data WHERE user_id = ? ORDER BY time ASC LIMIT ?", 
                 (user_id, num_records))
        data = c.fetchall()

    if not data:
        raise ValueError("沒有可用的數據來生成圖表。")

    times = [record['time'] for record in data]
    weights = [record['weight'] for record in data]
    bmis = [record['bmi'] for record in data]

    # 創建包含兩個子圖的圖表
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 10))
    
    # 繪製體重變化圖
    ax1.plot(times, weights, marker='o', linestyle='-', color='b')
    ax1.set_title('Weight trend over time')
    ax1.set_xlabel('Time')
    ax1.set_ylabel('Weight (kg)')
    ax1.tick_params(axis='x', rotation=45)
    
    # 繪製BMI變化圖
    ax2.plot(times, bmis, marker='o', linestyle='-', color='g')
    ax2.set_title('BMI trend over time')
    ax2.set_xlabel('Time')
    ax2.set_ylabel('BMI')
    ax2.tick_params(axis='x', rotation=45)
    
    # 添加BMI區間參考線
    ax2.axhline(y=18.5, color='r', linestyle='--', alpha=0.5)
    ax2.axhline(y=24, color='r', linestyle='--', alpha=0.5)
    ax2.fill_between(times, [18.5]*len(times), [24]*len(times), alpha=0.2, color='g')
    
    plt.tight_layout()

    # 生成唯一的檔名
    filename = f"{user_id}_{uuid.uuid4().hex}.png"
    img_path = os.path.join('img', filename)
    plt.savefig(img_path)
    plt.close()

    print(f"圖表已保存至 {img_path}")

    # 生成圖片的URL
    server_url = os.getenv("SERVER_URL")
    if not server_url:
        raise ValueError("SERVER_URL 環境變數未設置。")

    image_url = f"{server_url}/img/{filename}"
    print(f"圖表的URL：{image_url}")
    return image_url

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
