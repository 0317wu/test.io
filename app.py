import os
from flask import Flask, request, abort, send_from_directory
from dotenv import load_dotenv
from linebot import LineBotApi, WebhookHandler
from linebot.models import (
    MessageEvent, TextMessage, FollowEvent, TextSendMessage,
    LocationMessage, ImageSendMessage, TemplateSendMessage, ButtonsTemplate, PostbackAction
)
import logging
import matplotlib.pyplot as plt
import uuid

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

# 載入環境變數  
load_dotenv()
app = Flask(__name__)

# 初始化 LINE Bot API
line_bot_api = LineBotApi(os.getenv('LINE_CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.getenv('LINE_CHANNEL_SECRET'))

# 資料庫檔案位置
DATABASE = 'user_body_data.db'

# 儲存使用者狀態
user_states = {}

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

# 處理使用者的訊息事件
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    user_message = event.message.text.strip()

    # 若使用者有狀態
    if user_id in user_states:
        state = user_states[user_id]
        if state.get('state') == 'awaiting_body_record_input':
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

    # 根據使用者輸入呼叫對應功能
    if user_message == "開始":
        main_menu = (
            "🏋️‍♂️ 主選單：\n"
            "1️⃣ 運動目標\n"
            "2️⃣ 體態紀錄\n"
            "3️⃣ 運動指導\n"
            "4️⃣ AI 回答\n"
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
        user_states[user_id] = {'state': 'awaiting_body_record_input'}
        prompt_body_record_input(event, line_bot_api)
    elif user_message == "查詢紀錄":
        # 顯示第一頁紀錄，並在 show_body_records 中設定狀態
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

    # 新增對「上一頁 / 下一頁」指令的處理
    elif user_message == "體態紀錄上一頁":
        handle_body_record_pagination(event, "上一頁", line_bot_api, user_states, DATABASE)
    elif user_message == "體態紀錄下一頁":
        handle_body_record_pagination(event, "下一頁", line_bot_api, user_states, DATABASE)

    elif user_message == "飲食管理":
        handle_diet_guidance(event, line_bot_api, DATABASE)

    elif user_message in ["訓練計劃", "📋 訓練計劃"]:
        show_training_plan_menu(event, line_bot_api)
    elif user_message == "運動指導":
        show_exercise_guidance(event, line_bot_api)

    elif user_message in [ "查看初學者訓練計劃", "初學者運動指導計劃"]:
        show_beginner_training_plan(event, line_bot_api)
    elif user_message in ["中級者訓練計劃", "中級者運動指導計劃"]:
        show_intermediate_training_plan(event, line_bot_api)
    elif user_message in ["高級者訓練計劃", "高級者運動指導計劃"]:
        show_advanced_training_plan(event, line_bot_api)

    # 新增 AI 回答功能
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
        with get_db_connection(database) as conn:
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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
