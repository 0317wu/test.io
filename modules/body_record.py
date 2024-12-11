
import sqlite3
from datetime import datetime
from linebot.models import TextSendMessage, TemplateSendMessage, ButtonsTemplate, FlexSendMessage

PAGE_SIZE = 10

# 資料庫連接上下文管理器
def get_db_connection(database):
    conn = sqlite3.connect(database)
    conn.row_factory = sqlite3.Row
    return conn

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

def handle_body_record_input(event, line_bot_api, database, weight, height):
    user_id = event.source.user_id
    height_m = height / 100
    bmi = weight / (height_m ** 2)
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 儲存到資料庫
    with get_db_connection(database) as conn:
        c = conn.cursor()
        c.execute('''INSERT INTO body_data (user_id, weight, height, bmi, time)
                     VALUES (?, ?, ?, ?, ?)''', 
                  (user_id, weight, height, bmi, current_time))
        conn.commit()

    # 回應當筆紀錄
    reply_message = (
        f"✅ 體態紀錄成功！\n"
        f"📅 記錄時間：{current_time}\n"
        f"⚖️ 體重：{weight} kg\n"
        f"📏 身高：{height} cm\n"
        f"📊 BMI：{bmi:.2f}"
    )
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_message))

def show_body_records(event, line_bot_api, database, page=1):
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
            f"  ⚖️ 體重: {record['weight']} kg \n"
            f"  📏 身高: {record['height']} cm \n"
            f"  📊 BMI: {record['bmi']:.2f}\n\n"
        )

    # 計算總頁數
    total_pages = (total_records + PAGE_SIZE - 1) // PAGE_SIZE

    # 按鈕模板
    actions = []
    if page > 1:
        actions.append({"type": "message", "label": "⬅️ 上一頁", "text": "體態紀錄上一頁"})
    if page < total_pages:
        actions.append({"type": "message", "label": "下一頁 ➡️", "text": "體態紀錄下一頁"})

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
