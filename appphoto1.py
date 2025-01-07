import os
from flask import Flask, request, abort, send_from_directory
from dotenv import load_dotenv
from linebot import LineBotApi, WebhookHandler
from linebot.models import (
    MessageEvent, TextMessage, FollowEvent, TextSendMessage,
    LocationMessage, ImageSendMessage, ImageMessage
)
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
from PIL import Image  # Added for image processing

# 引入模組
from modules.diet_management import handle_diet_guidance
from modules.exercise_goal import (
    show_exercise_goal, show_fat_loss_plan,
    show_muscle_gain_plan, show_cardiovascular_plan
)
from modules.body_record import (
    show_body_record_menu, prompt_body_record_input, handle_body_record_input,
    show_body_records, handle_body_record_pagination, get_db_connection
)
from modules.exercise_guidance import (
    show_exercise_guidance, show_training_plan_menu,
    show_beginner_training_plan, show_intermediate_training_plan,
    show_advanced_training_plan
)
from modules.food_record import save_food_record, get_diet_records, initialize_database

# 載入環境變數
load_dotenv()
app = Flask(__name__)

# 初始化 LINE Bot API
line_bot_api = LineBotApi(os.getenv('LINE_CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.getenv('LINE_CHANNEL_SECRET'))

# 資料庫檔案位置
DATABASE = 'user_body_data.db'
CREATEALARM_DB = 'createalarm.db'
# 儲存使用者狀態
user_states = {}
AWAITING_BODY_RECORD_INPUT = 'awaiting_body_record_input'
AWAITING_FOOD_IMAGE = 'awaiting_food_image'

# 初始化 Google Generative AI (Gemini)
from google import generativeai
# 加載 Google Generative AI API 金鑰
google_api_key = os.getenv("GOOGLE_GENERATIVEAI_API_KEY")
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
    return send_from_directory(r'd:\\User\\Desktop\\BMICHART\\img', filename)

@app.route("/callback", methods=['POST'])
def callback():
    # 驗證 LINE 平台的請求
    signature = request.headers.get('X-Line-Signature')
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
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
    Prompts the user to upload a food image.
    
    Parameters:
    - event: The LINE event object.
    - line_bot_api: The LINE Bot API instance.
    """
    prompt_message = "🍽️ 請上傳您剛剛吃的食物照片。"
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=prompt_message))

# New Image Message Handler
@handler.add(MessageEvent, message=ImageMessage)
def handle_image_message(event):
    user_id = event.source.user_id
    # Check if the user is in a specific state
    if user_id in user_states:
        state = user_states[user_id].get('state')
        if state == AWAITING_FOOD_IMAGE:
            handle_food_image(event)
            return
        # Handle other states if necessary

    # Default image handling (existing functionality)
    try:
        message_content = line_bot_api.get_message_content(event.message.id)
        image_data = message_content.content
        logger.info(f"Received image with size: {len(image_data)} bytes.")
        # Process image using Gemini API and get response
        gemini_response = process_image_with_gemini(image_data)
        # Reply with text message
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=gemini_response))
    except Exception as e:
        logger.error(f"Error in image handling: {e}, traceback: {traceback.format_exc()}")
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="抱歉，發生了意外錯誤。"))

def process_image_with_gemini(image_data):
    """Sends image to Gemini and returns the processed response."""
    # Set up Gemini API client (replace with actual API setup)
    try:
        model = generativeai.GenerativeModel('gemini-1.5-flash')  # Updated model here, check with latest one from Google
        # Process image data (image_data is a byte array)
        try:
            image_file = Image.open(io.BytesIO(image_data))  # Convert bytes to image object
        except Exception as e:
            logger.error(f"Error opening image: {e}, traceback: {traceback.format_exc()}")
            return "抱歉，我遇到了打開圖片時的錯誤。"
        try:
            response = model.generate_content(
                [image_file, "Describe this image in great details."]
            )
            return response.text
        except Exception as e:
            logger.error(f"Error processing image with Gemini API: {e}, traceback: {traceback.format_exc()}")
            return "抱歉，我在使用 Gemini 處理圖片時遇到了錯誤。"
    except Exception as e:
        logger.error(f"General Error in process_image_with_gemini: {e}, traceback: {traceback.format_exc()}")
        return "抱歉，我在處理圖片時遇到了錯誤。"

def handle_food_image(event):
    user_id = event.source.user_id
    try:
        # Get the image content
        message_content = line_bot_api.get_message_content(event.message.id)
        image_data = message_content.content
        logger.info(f"Received food image with size: {len(image_data)} bytes.")

        # Process image using Gemini API to recognize food items
        food_items = recognize_food_items(image_data)

        if not food_items:
            reply_text = "抱歉，我無法辨識這張圖片中的食物。請再試一次或提供更清晰的照片。"
        else:
            # Save recognized food items into diet records
            save_food_record(user_id, food_items)
            # Prepare reply message
            food_list = "\n".join([f"- {food}" for food in food_items])
            reply_text = f"已成功記錄以下食物：\n{food_list}"
        
        # Reply to the user
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))
    except Exception as e:
        logger.error(f"Error handling food image: {e}, traceback: {traceback.format_exc()}")
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="抱歉，處理食物照片時發生錯誤。"))
    finally:
        # Reset user state
        if user_id in user_states:
            del user_states[user_id]

def recognize_food_items(image_data):
    """
    Uses Gemini to recognize food items in the image.

    Parameters:
    - image_data (bytes): The image data in bytes.

    Returns:
    - list of str: List of recognized food items.
    """
    try:
        # Initialize the Gemini model for image recognition
        model = generativeai.GenerativeModel('gemini-2.0-flash-exp')  # Use appropriate model

        # Convert image data to PIL Image
        image_file = Image.open(io.BytesIO(image_data))

        # Generate a prompt for Gemini to recognize food items
        prompt = "Identify all the food items present in this image."

        # Send image and prompt to Gemini
        response = model.generate_content([image_file, prompt])

        # Extract food items from the response
        # This assumes that Gemini returns a comma-separated list of food items
        food_items = [item.strip() for item in response.text.split(',') if item.strip()]
        
        logger.info(f"Recognized food items: {food_items}")
        return food_items
    except Exception as e:
        logger.error(f"Error recognizing food items with Gemini: {e}, traceback: {traceback.format_exc()}")
        return []

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    user_message = event.message.text.strip()

    # Handle user state
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
            # Should not receive text while awaiting image
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="🍽️ 請上傳您剛剛吃的食物照片。或者輸入「取消」以取消。"))
            return

    # Main menu and other commands
    if user_message == "開始":
        main_menu = (
            "🏋️‍♂️ 主選單：\n"
            "1️⃣ 運動目標\n"
            "2️⃣ 體態紀錄\n"
            "3️⃣ 運動指導\n"
            "4️⃣ 飲食管理\n"
            "5️⃣ AI 回答\n"
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
            image_message = ImageSendMessage(
                original_content_url=image_url,
                preview_image_url=image_url
            )
            line_bot_api.reply_message(event.reply_token, image_message)
        except Exception as e:
            logger.error(f"圖表生成錯誤: {e}")
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="⚠️ 體重和BMI變化圖表生成失敗。"))

    elif user_message == "體態紀錄上一頁":
        handle_body_record_pagination(event, "上一頁", line_bot_api, user_states, DATABASE)
    elif user_message == "體態紀錄下一頁":
        handle_body_record_pagination(event, "下一頁", line_bot_api, user_states, DATABASE)

    elif user_message == "飲食管理":
        diet_menu = (
            "🍎 飲食管理：\n"
            "1️⃣ 記錄食物\n"
            "2️⃣ 查看飲食紀錄\n"
            "請輸入對應選項。"
        )
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=diet_menu))

    elif user_message == "記錄食物":
        user_states[user_id] = {'state': AWAITING_FOOD_IMAGE}
        prompt_food_image_input(event, line_bot_api)

    elif user_message == "查看飲食紀錄":
        try:
            records = get_diet_records(user_id)
            if not records:
                reply_text = "您目前沒有任何飲食紀錄。"
            else:
                reply_text = "📋 您的飲食紀錄：\n"
                for record in records:
                    timestamp = datetime.fromisoformat(record['timestamp']).strftime('%Y-%m-%d %H:%M')
                    reply_text += f"{timestamp}: {record['food_item']}\n"
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))
        except Exception as e:
            logger.error(f"Error retrieving diet records: {e}")
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="抱歉，無法獲取您的飲食紀錄。"))

    elif user_message == "運動指導":
        show_exercise_guidance(event, line_bot_api)

    elif user_message in ["訓練計劃", "📋 訓練計劃"]:
        show_training_plan_menu(event, line_bot_api)
    elif user_message in [ "查看初學者訓練計劃", "初學者運動指導計劃"]:
        show_beginner_training_plan(event, line_bot_api)
    elif user_message in ["中級者訓練計劃", "中級者運動指導計劃"]:
        show_intermediate_training_plan(event, line_bot_api)
    elif user_message in ["高級者訓練計劃", "高級者運動指導計劃"]:
        show_advanced_training_plan(event, line_bot_api)

    # AI Answering Function
    elif user_message.startswith("AI "):
        user_query = user_message[3:].strip()
        if not user_query:
            reply_text = "❌ 請在「AI」後面輸入您的問題。例如：AI 什麼是增肌？"
        else:
            try:
                response = generativeai.GenerativeModel('gemini-2.0-flash-exp').generate_content(user_query)
                reply_text = response.text
            except Exception as e:
                logger.error(f"Gemini Error: {e}")
                reply_text = "❌ 發生錯誤，請稍後再試。"
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))

    else:
        # Handle undefined commands
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
        with get_db_connection(database) as conn:
            c = conn.cursor()
            c.execute(
                "SELECT time, weight, bmi FROM body_data WHERE user_id = ? ORDER BY time ASC LIMIT ?", 
                (user_id, num_records)
            )
            data = c.fetchall()

        if not data:
            raise ValueError("沒有可用的數據來生成圖表")

        times = [record[0] for record in data]
        weights = [record[1] for record in data]
        bmis = [record[2] for record in data]

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
initialize_database()  # Initialize food_record.db
load_and_schedule_existing_reminders()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
