# app.py

import os
from flask import Flask, request, abort, send_from_directory
from dotenv import load_dotenv
from linebot import LineBotApi, WebhookHandler
from linebot.models import (
    MessageEvent, TextMessage, FollowEvent, TextSendMessage,
    ImageMessage, LocationMessage
)
from linebot.exceptions import InvalidSignatureError
import logging
import matplotlib.pyplot as plt
import uuid
import traceback
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
from datetime import datetime
import sqlite3
import atexit
import io
from PIL import Image  # 用於圖像處理
import json

# 引入模組
from modules.diet_management import handle_diet_guidance
from modules.exercise_goal import (
    show_exercise_goal, show_fat_loss_plan,
    show_muscle_gain_plan, show_cardiovascular_plan
)
from modules.body_record import (
    show_body_record_menu, prompt_body_record_input, handle_body_record_input,
    show_body_records, handle_body_record_pagination, get_db_connection as get_body_db_connection
)
from modules.exercise_guidance import (
    show_exercise_guidance, show_training_plan_menu,
    show_beginner_training_plan, show_intermediate_training_plan,
    show_advanced_training_plan
)
from modules.food_record import save_food_record, get_diet_records, initialize_database, recognize_food_items,save_manual_food_record
load_dotenv()
app = Flask(__name__)

# 初始化 LINE Bot API
line_bot_api = LineBotApi(os.getenv('LINE_CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.getenv('LINE_CHANNEL_SECRET'))

# 資料庫檔案位置
DATABASE = 'user_body_data.db'      # 用於體態紀錄
CREATEALARM_DB = 'createalarm.db'   # 用於提醒功能
FOOD_RECORD_DB = 'food_record.db'   # 用於飲食紀錄

# 儲存使用者狀態
user_states = {}
AWAITING_BODY_RECORD_INPUT = 'awaiting_body_record_input'
AWAITING_FOOD_IMAGE = 'awaiting_food_image'

# 初始化 Google Generative AI (Gemini)
from google import generativeai
# 加載 Google Generative AI API 金鑰
google_api_key = os.getenv("GOOGLE_GENERATIVEAI_API_KEY")
if not google_api_key:
    raise ValueError("GOOGLE_GENERATIVEAI_API_KEY 未設置。")
generativeai.configure(api_key=google_api_key)

# 確保 img 目錄存在
if not os.path.exists('img'):
    os.makedirs('img')

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 初始化 Scheduler
scheduler = BackgroundScheduler()
scheduler.start()

# 確保應用結束時關閉 Scheduler
atexit.register(lambda: scheduler.shutdown())

# 新增從伺服器提供圖片的路由
@app.route('/img/<filename>')
def serve_image(filename):
    return send_from_directory('img', filename)

@app.route("/callback", methods=['POST'])
def callback():
    # 驗證 LINE 平台的請求
    signature = request.headers.get('X-Line-Signature')
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        logger.error("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)
    except Exception as e:
        logger.error(f"Error handling request: {e}")
        abort(400)
    return 'OK'

# 處理首次加入機器人的事件
@handler.add(FollowEvent)
def handle_follow(event):
    welcome_message = "🎉 歡迎使用健身助手！請傳送「開始」以進入主選單。"
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=welcome_message))



# Prompt Function for Food Image Input
def prompt_food_image_input(event, line_bot_api):
    """
    提示使用者上傳食物圖片。
    
    參數:
    - event: LINE 事件對象。
    - line_bot_api: LINE Bot API 實例。
    """
    prompt_message = "🍽️ 請上傳您剛剛吃的食物照片。"
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=prompt_message))

# 新增圖片訊息處理器
@handler.add(MessageEvent, message=ImageMessage)
def handle_image_message(event):
    user_id = event.source.user_id
    # 檢查使用者是否處於特定狀態
    if user_id in user_states:
        state = user_states[user_id].get('state')
        if state == AWAITING_FOOD_IMAGE:
            handle_food_image(event)
            return
        # 可在此處處理其他狀態

    # 預設的圖片處理（現有功能）
    try:
        message_content = line_bot_api.get_message_content(event.message.id)
        image_data = message_content.content
        logger.info(f"接收到用戶 {user_id} 的圖片，大小：{len(image_data)} bytes。")
        # 使用 Gemini API 處理圖片並獲取回應
        gemini_response = process_image_with_gemini(image_data)
        # 回應使用者
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=gemini_response))
    except Exception as e:
        logger.error(f"圖片處理時出錯: {e}, traceback: {traceback.format_exc()}")
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="抱歉，發生了意外錯誤。"))
        

def process_image_with_gemini(image_data):
    """將圖片發送至 Gemini，根據內容分類返回食物信息或物品用途描述。"""
    try:
        model = generativeai.GenerativeModel('gemini-2.0-flash-exp')  # 更新為最新的模型

        # 處理圖片數據
        try:
            image_file = Image.open(io.BytesIO(image_data))  # 將位元組轉換為圖片對象
        except Exception as e:
            logger.error(f"打開圖片時出錯: {e}, traceback: {traceback.format_exc()}")
            return "抱歉，我遇到了打開圖片時的錯誤。"

        try:
            # Step 1: 分類圖片內容（食物 or 其他物品）
            classification_prompt = (
                "Classify the content of this image as either 'food' or 'other items'. "
                "Respond only with 'food' or 'other items'."
            )
            classification_response = model.generate_content([image_file, classification_prompt])
            content_type = classification_response.text.strip().lower()

            # Step 2: 根據分類結果選擇提示
            if content_type == "food":
                prompt = (
                    "Identify all the food items present in this image and provide the estimated calories for each item. "
                    "Respond only with a JSON array in the following format without any additional text:\n\n"
                    "[\n"
                    "    {\n"
                    '        "food_item": "Food Name",\n'
                    '        "calories": Estimated Calories\n'
                    "    },\n"
                    "    ...\n"
                    "]"
                )
            else:
                prompt = (
                    "Identify all the items present in this image and describe their primary usage or how they can be used. "
                    "Respond only with a JSON array in the following format without any additional text:\n\n"
                    "[\n"
                    "    {\n"
                    '        "item": "Item Name",\n'
                    '        "usage": "Description of how to use the item"\n'
                    "    },\n"
                    "    ...\n"
                    "]"
                )

            # Step 3: 處理圖片並返回結果
            response = model.generate_content([image_file, prompt])
            return response.text

        except Exception as e:
            logger.error(f"使用 Gemini API 處理圖片時出錯: {e}, traceback: {traceback.format_exc()}")
            return "抱歉，我在使用 Gemini 處理圖片時遇到了錯誤。"

    except Exception as e:
        logger.error(f"General Error in process_image_with_gemini: {e}, traceback: {traceback.format_exc()}")
        return "抱歉，我在處理圖片時遇到了錯誤。"


def handle_food_image(event):
    user_id = event.source.user_id
    try:
        # 獲取圖片內容
        message_content = line_bot_api.get_message_content(event.message.id)
        image_data = message_content.content
        logger.info(f"接收到用戶 {user_id} 的食物圖片，大小：{len(image_data)} bytes。")

        # 使用 Gemini API 辨識食物項目及其熱量
        food_items = recognize_food_items(image_data)

        # 添加日誌以確認 food_items 的結構
        logger.debug(f"food_items 的類型：{type(food_items)}")
        logger.debug(f"food_items 的內容：{food_items}")

        if not food_items:
            reply_text = "抱歉，我無法辨識這張圖片中的食物或計算熱量。請再試一次或提供更清晰的照片。"
        else:
            # 儲存食物紀錄及熱量
            save_food_record(user_id, food_items)

            # 準備回應訊息，包括每個食物的熱量
            food_details = "\n".join([f"- {item['food_item']}: {item['calories']} 千卡" for item in food_items])
            total_calories = sum([item['calories'] for item in food_items])
            reply_text = f"已成功記錄以下食物及其熱量：\n{food_details}\n\n總攝取熱量：{total_calories} 千卡"

        # 回應使用者
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))
    except Exception as e:
        logger.error(f"處理用戶 {user_id} 的食物圖片時出錯: {e}, traceback: {traceback.format_exc()}")
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="抱歉，處理食物照片時發生錯誤。請稍後再試。"))
    finally:
        # 重置使用者狀態
        if user_id in user_states:
            del user_states[user_id]

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    user_message = event.message.text.strip()

    # 處理使用者狀態
    if user_id in user_states:
        state = user_states[user_id].get('state')
        if state == AWAITING_BODY_RECORD_INPUT:
            if user_message.lower() in ["取消", "返回"]:
                del user_states[user_id]
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text="❌ 已取消體態紀錄。"))
                return
            try:
                weight, height = map(float, user_message.split())
                handle_body_record_input(event, line_bot_api, DATABASE, weight, height)
                del user_states[user_id]
            except ValueError:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text="❌ 請按照正確格式輸入，例如：80 180"))
            return
        elif state == AWAITING_FOOD_IMAGE:
            # 當使用者處於等待上傳食物圖片狀態時，提醒其上傳圖片
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="🍽️ 請上傳您剛剛吃的食物照片。或者輸入「取消」以取消。"))
            return

    # 主選單和其他指令
    if user_message == "開始":
        main_menu = (
            "🏋️‍♂️ 主選單：\n"
            "1️⃣ 飲食管理\n"
            "2️⃣ 運動紀錄\n"
            "3️⃣ 運動目標\n"
            "4️⃣ 運動指導\n"
            "5️⃣ AI 回答(輸入AI 想問的東西)\n"
            "6️⃣提醒\n"
            "7️⃣飲食紀錄\n"
            "8️⃣AI圖片辨識\n"
            "請輸入對應選項。"
        )
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=main_menu))

    elif user_message == "運動目標":
        show_exercise_goal(event, line_bot_api)
    elif user_message == "減脂":
        show_fat_loss_plan(event, line_bot_api)
    elif user_message == "增肌":
        show_muscle_gain_plan(event, line_bot_api)
    elif user_message == "提高心肺功能":
        show_cardiovascular_plan(event, line_bot_api)

    elif user_message == "體態紀錄":
        show_body_record_menu(event, line_bot_api)
    elif user_message == "輸入紀錄":
        user_states[user_id] = {'state': AWAITING_BODY_RECORD_INPUT}
        prompt_body_record_input(event, line_bot_api)
    elif user_message == "查詢紀錄":
        show_body_records(event, line_bot_api, DATABASE, page=1, user_states=user_states)
    elif user_message == "顯示體重圖表":
        try:
            image_url = generate_weight_and_bmi_charts(user_id, DATABASE)
            image_message = line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=f"圖表已生成，請點擊以下連結查看：{image_url}")
            )
        except Exception as e:
            logger.error(f"圖表生成錯誤: {e}")
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="⚠️ 體重和BMI變化圖表生成失敗。"))

    elif user_message == "體態紀錄上一頁":
        handle_body_record_pagination(event, "上一頁", line_bot_api, user_states, DATABASE)
    elif user_message == "體態紀錄下一頁":
        handle_body_record_pagination(event, "下一頁", line_bot_api, user_states, DATABASE)

    elif user_message == "飲食紀錄":
        diet_menu = (
            "🍎 飲食紀錄：\n"
            "1️⃣ 記錄食物\n"
            "2️⃣ 手動記錄食物\n"
            "3️⃣ 查看飲食紀錄\n"
            "請輸入對應選項。"
        )
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=diet_menu))

    elif user_message == "記錄食物":
        user_states[user_id] = {'state': AWAITING_FOOD_IMAGE}
        prompt_food_image_input(event, line_bot_api)
    elif user_message == "手動記錄食物":
        save_manual_food_record(event, line_bot_api)

    elif user_message == "查看飲食紀錄":
        try:
            records = get_diet_records(user_id)
            if not records:
                reply_text = "您目前沒有任何飲食紀錄。"
            else:
                reply_text = "📋 您的飲食紀錄：\n"
                total_calories = 0
                for record in records:
                    timestamp = datetime.fromisoformat(record['timestamp']).strftime('%Y-%m-%d %H:%M')
                    food = record['food_item']
                    calories = record['calories']
                    total_calories += calories
                    reply_text += f"{timestamp}: {food} - {calories} 千卡\n"
                reply_text += f"\n總攝取熱量：{total_calories} 千卡"
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))
        except Exception as e:
            logger.error(f"獲取用戶 {user_id} 的飲食紀錄時出錯: {e}")
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="抱歉，無法獲取您的飲食紀錄。"))

    elif user_message == "運動指導":
        show_exercise_guidance(event, line_bot_api)
    elif user_message == "飲食管理":
        handle_diet_guidance(event, line_bot_api, DATABASE)
    elif user_message in ["訓練計劃", "📋 訓練計劃"]:
        show_training_plan_menu(event, line_bot_api)
    elif user_message in ["查看初學者訓練計劃", "初學者運動指導計劃"]:
        show_beginner_training_plan(event, line_bot_api)
    elif user_message in ["中級者訓練計劃", "中級者運動指導計劃"]:
        show_intermediate_training_plan(event, line_bot_api)
    elif user_message in ["高級者訓練計劃", "高級者運動指導計劃"]:
        show_advanced_training_plan(event, line_bot_api)

    # AI 回答功能
    elif user_message.startswith("AI "):
        user_query = user_message[3:].strip()
        if not user_query:
            reply_text = "❌ 請在「AI」後面輸入您的問題。例如：AI 什麼是增肌？"
        else:
            try:
                response = generativeai.GenerativeModel('gemini-2.0-flash-exp').generate_content([user_query])
                reply_text = response.text
            except Exception as e:
                logger.error(f"Gemini 錯誤: {e}")
                reply_text = "❌ 發生錯誤，請稍後再試。"
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))

    else:
        # 處理未定義的指令
        default_reply = "抱歉，我不太明白您的意思。請選擇主選單中的選項。"
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=default_reply))

@handler.add(MessageEvent, message=LocationMessage)
def handle_location_message(event):
    gym_search_url = "https://www.google.com/maps/search/?api=1&query=gym"
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=f"你可以在這裡找到附近的健身房: {gym_search_url}")
    )

def generate_weight_and_bmi_charts(user_id, database, num_records=10):
    try:
        logger.info(f"開始為用戶 {user_id} 生成圖表")
        
        # 從資料庫獲取數據
        with get_body_db_connection(database) as conn:
            c = conn.cursor()
            c.execute(
                "SELECT time, weight, bmi FROM body_data WHERE user_id = ? ORDER BY time ASC LIMIT ?", 
                (user_id, num_records)
            )
            data = c.fetchall()

        if not data:
            raise ValueError("沒有可用的數據來生成圖表")

        times = [record['time'] for record in data]
        weights = [record['weight'] for record in data]
        bmis = [record['bmi'] for record in data]

        # 創建圖表
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 10))
        
        # 繪製體重變化圖
        ax1.plot(times, weights, marker='o', linestyle='-', color='b')
        ax1.set_title('Weight trend over time')
        ax1.set_xlabel('TIME')
        ax1.set_ylabel('WEIGHT (kg)')
        ax1.tick_params(axis='x', rotation=45)
        
        # 繪製BMI變化圖
        ax2.plot(times, bmis, marker='o', linestyle='-', color='g')
        ax2.set_title('BMI trend over time')
        ax2.set_xlabel('TIME')
        ax2.set_ylabel('BMI')
        ax2.tick_params(axis='x', rotation=45)
        
        plt.tight_layout()

        # 生成唯一的檔名和路徑
        filename = f"{user_id}_{uuid.uuid4().hex}.png"
        img_path = os.path.join('img', filename)
        plt.savefig(img_path)
        plt.close()
        
        # 生成圖片URL
        server_url = os.getenv("SERVER_URL")
        if not server_url:
            raise ValueError("SERVER_URL 環境變數未設置")
            
        image_url = f"{server_url}/img/{filename}"
        logger.info(f"圖表成功生成：{img_path}")
        return image_url
            
    except Exception as e:
        logger.error(f"生成圖表時發生錯誤：{str(e)}")
        raise

def save_reminder(user_id, reminder_time, message):
    conn = sqlite3.connect(CREATEALARM_DB)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            reminder_time TEXT NOT NULL,
            message TEXT NOT NULL
        );
    ''')
    cursor.execute('''
        INSERT INTO reminders (user_id, reminder_time, message)
        VALUES (?, ?, ?)
    ''', (user_id, reminder_time.isoformat(), message))
    conn.commit()
    conn.close()
    logger.info(f"已儲存提醒：用戶 {user_id}, 時間 {reminder_time}, 訊息 '{message}'")

def send_reminder(user_id, message):
    try:
        line_bot_api.push_message(user_id, TextSendMessage(text=f"⏰ 提醒：{message}"))
        logger.info(f"已發送提醒給用戶 {user_id}: {message}")
    except Exception as e:
        logger.error(f"發送提醒時出錯：{e}")

def schedule_reminder(user_id, reminder_time, message):
    trigger = DateTrigger(run_date=reminder_time)
    job_id = f"reminder_{user_id}_{uuid.uuid4().hex}"
    scheduler.add_job(send_reminder, trigger, args=[user_id, message], id=job_id)
    logger.info(f"已排程提醒：用戶 {user_id}, 時間 {reminder_time}, 訊息 '{message}', Job ID: {job_id}")

def load_and_schedule_existing_reminders():
    conn = sqlite3.connect(CREATEALARM_DB)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            reminder_time TEXT NOT NULL,
            message TEXT NOT NULL
        );
    ''')
    cursor.execute('''
        SELECT user_id, reminder_time, message FROM reminders
        WHERE datetime(reminder_time) > datetime('now')
    ''')
    reminders = cursor.fetchall()
    conn.close()
    
    for reminder in reminders:
        user_id, reminder_time_str, message = reminder
        reminder_time = datetime.fromisoformat(reminder_time_str)
        schedule_reminder(user_id, reminder_time, message)
    logger.info("已載入並排程所有現有的提醒。")

# 在應用啟動後調用
initialize_database()  # 初始化 food_record.db
load_and_schedule_existing_reminders()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
