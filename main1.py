import os
import sqlite3
from datetime import datetime
from linebot import LineBotApi, WebhookHandler
from linebot.models import FlexSendMessage, TextSendMessage
from flask import Flask, request, abort
from dotenv import load_dotenv
from linebot.models import MessageEvent, TextMessage
from diet import generate_daily_menu, generate_menu, calculate_bmi

# 載入環境變數
load_dotenv()
app = Flask(__name__)

# LINE BOT API 初始化
line_bot_api = LineBotApi(os.getenv('LINE_CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.getenv('LINE_CHANNEL_SECRET'))

# 運動計劃
運動計劃 = {
    "初學者": ["伏地挺身：10次", "深蹲：15次", "平板支撐：30秒"],
    "中級者": ["伏地挺身：20次", "深蹲：25次", "平板支撐：60秒"],
    "高級者": ["伏地挺身：30次", "深蹲：40次", "平板支撐：90秒"]
}

# 運動影片連結
運動影片 = {
    "伏地挺身": "https://www.youtube.com/watch?v=IODxDxX7oi4",
    "深蹲": "https://www.youtube.com/watch?v=aclHkVaku9U",
    "引體向上": "https://www.youtube.com/watch?v=9N4oPlpgf9w",
    "仰臥起坐": "https://www.youtube.com/watch?v=MKmrqcoCZ-M"
}

# 用來儲存資料庫連接
DATABASE = 'user_body_data.db'

# 創建資料庫連接
def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # 這樣就可以用字典形式來操作資料
    return conn

# 初始化資料庫，創建表格
def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS body_data (
                    user_id TEXT,
                    weight REAL,
                    height REAL,
                    bmi REAL,
                    time TEXT)''')
    conn.commit()
    conn.close()

# 初始化資料庫
init_db()

@app.route("/callback", methods=['POST'])
def callback():
    # 驗證 LINE 平台的請求
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except Exception as e:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text

    if user_message == "運動目標":
        # 回傳包含 Google Maps 健身房搜尋的 URL
        gym_search_url = "https://www.google.com/maps/search/?api=1&query=gym"
        reply_message = TextSendMessage(
            text=f"點擊以下連結查看附近的健身房：\n{gym_search_url}"
        )
        line_bot_api.reply_message(event.reply_token, reply_message)

    elif user_message == "運動指導":
        # 回傳運動計劃的 Flex Message
        flex_message = FlexSendMessage(
            alt_text="運動指南選單",
            contents={
                "type": "carousel",
                "contents": [
                    {
                        "type": "bubble",
                        "body": {
                            "type": "box",
                            "layout": "vertical",
                            "contents": [
                                {"type": "text", "text": "運動計劃", "weight": "bold", "size": "xl"},
                                {"type": "text", "text": "選擇等級來查看計劃"}
                            ]
                        },
                        "footer": {
                            "type": "box",
                            "layout": "vertical",
                            "spacing": "sm",
                            "contents": [
                                {"type": "button", "style": "primary", "action": {"type": "message", "label": "初學者", "text": "初學者"}},
                                {"type": "button", "style": "primary", "action": {"type": "message", "label": "中級者", "text": "中級者"}},
                                {"type": "button", "style": "primary", "action": {"type": "message", "label": "高級者", "text": "高級者"}} ,
                                {"type": "button", "style": "primary", "action": {"type": "message", "label": "運動教學", "text": "運動教學"}}
                            ]
                        }
                    }
                ]
            }
        )
        line_bot_api.reply_message(event.reply_token, flex_message)

    elif user_message in 運動計劃:
        # 回傳對應等級的運動計劃
        計劃內容 = "\n".join(運動計劃[user_message])
        reply_message = f"適合 {user_message} 的運動計劃：\n{計劃內容}"
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_message))

    elif user_message == "運動教學":
        # 顯示運動教學的 Flex Message
        flex_message = FlexSendMessage(
            alt_text="運動教學",
            contents={
                "type": "carousel",
                "contents": [
                    {
                        "type": "bubble",
                        "body": {
                            "type": "box",
                            "layout": "vertical",
                            "contents": [
                                {"type": "text", "text": "運動教學", "weight": "bold", "size": "xl"},
                                {"type": "text", "text": "選擇運動來查看教學"}
                            ]
                        },
                        "footer": {
                            "type": "box",
                            "layout": "vertical",
                            "spacing": "sm",
                            "contents": [
                                {"type": "button", "style": "primary", "action": {"type": "message", "label": "深蹲", "text": "深蹲"}},
                                {"type": "button", "style": "primary", "action": {"type": "message", "label": "伏地挺身", "text": "伏地挺身"}},
                                {"type": "button", "style": "primary", "action": {"type": "message", "label": "仰臥起坐", "text": "仰臥起坐"}},
                                {"type": "button", "style": "primary", "action": {"type": "message", "label": "引體向上", "text": "引體向上"}}
                            ]
                        }
                    }
                ]
            }
        )
        line_bot_api.reply_message(event.reply_token, flex_message)

    elif user_message in 運動影片:
        # 回傳對應的影片連結
        video_url = 運動影片[user_message]
        reply_message = f"這是 {user_message} 的教學影片：\n{video_url}"
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_message))

    elif user_message.startswith("體態紀錄"):
        try:
            # 假設用戶輸入格式: 體態紀錄 70 1.75（體重、身高）
            _, weight, height = user_message.split()
            weight = float(weight)
            height = float(height)
            
            # 計算 BMI
            bmi = calculate_bmi(weight, height)
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # 儲存紀錄到 SQLite 資料庫
            user_id = event.source.user_id
            conn = get_db()
            c = conn.cursor()
            c.execute('''INSERT INTO body_data (user_id, weight, height, bmi, time)
                         VALUES (?, ?, ?, ?, ?)''', 
                         (user_id, weight, height, bmi, current_time))
            conn.commit()
            conn.close()
            
            # 顯示體態紀錄
            reply_message = f"您的 BMI 為 {bmi:.2f}，記錄時間：{current_time}\n"
            reply_message += "您的紀錄如下：\n"
            
            # 查詢所有紀錄
            conn = get_db()
            c = conn.cursor()
            c.execute("SELECT * FROM body_data WHERE user_id = ?", (user_id,))
            records = c.fetchall()
            for record in records:
                reply_message += f"時間: {record['time']} | 體重: {record['weight']} | 身高: {record['height']} | BMI: {record['bmi']:.2f}\n"
            conn.close()

            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_message))

        except Exception as e:
            # 處理格式錯誤或其他問題
            error_message = TextSendMessage(text="請按照正確格式輸入：體態紀錄 體重(公斤) 身高(公尺)")
            line_bot_api.reply_message(event.reply_token, error_message)
    else:
        # 回傳預設訊息
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="請點選有效指令！"))

if __name__ == "__main__":
    app.run(port=5000)
