import os
from flask import Flask, request, abort
from dotenv import load_dotenv
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, FollowEvent, TextSendMessage

# 引入模組
from modules.exercise_goal import show_exercise_goal, show_fat_loss_plan, show_muscle_gain_plan, show_cardiovascular_plan
from modules.body_record import show_body_record_menu, prompt_body_record_input, handle_body_record_input, show_body_records
from modules.exercise_guidance import show_exercise_guidance, show_diet_guidance_menu, show_training_plan_menu, show_beginner_diet_plan, show_intermediate_diet_plan, show_advanced_diet_plan, show_beginner_training_plan, show_intermediate_training_plan, show_advanced_training_plan

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

@app.route("/callback", methods=['POST'])
def callback():
    # 驗證 LINE 平台的請求
    signature = request.headers.get('X-Line-Signature')
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except Exception as e:
        print(f"Error: {e}")
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

    # 處理「體態紀錄」相關的狀態
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
                del user_states[user_id]  # 清除狀態
            except ValueError:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text="❌ 請按照正確格式輸入，例如：80 180"))
            return

    # 根據使用者輸入呼叫對應功能
    if user_message == "開始":
        main_menu = "🏋️‍♂️ 主選單：\n1️⃣ 運動目標\n2️⃣ 體態紀錄\n3️⃣ 運動指導\n請輸入對應選項。"
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
        show_body_records(event, line_bot_api, DATABASE)
    elif user_message == "運動指導":
        show_exercise_guidance(event, line_bot_api)
    elif user_message in ["飲食指導", "🍎 飲食指導"]:
        show_diet_guidance_menu(event, line_bot_api)
    elif user_message in ["訓練計劃", "📋 訓練計劃"]:
        show_training_plan_menu(event, line_bot_api)
    elif user_message in ["初階者飲食方案", "👶 初階者飲食方案"]:
        show_beginner_diet_plan(event, line_bot_api)
    elif user_message in ["中級者飲食方案", "💪 中級者飲食方案"]:
        show_intermediate_diet_plan(event, line_bot_api)
    elif user_message in ["高級者飲食方案", "🔥 高級者飲食方案"]:
        show_advanced_diet_plan(event, line_bot_api)
    elif user_message in ["初學者訓練計劃", "👶 初學者訓練計劃"]:
        show_beginner_training_plan(event, line_bot_api)
    elif user_message in ["中級者訓練計劃", "💪 中級者訓練計劃"]:
        show_intermediate_training_plan(event, line_bot_api)
    elif user_message in ["高級者訓練計劃", "🔥 高級者訓練計劃"]:
        show_advanced_training_plan(event, line_bot_api)
    else:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="❌ 未知的選項，請重新輸入。"))

if __name__ == "__main__":
    # 建議在生產環境中使用 gunicorn 或其他更安全的服務器
    app.run(host="0.0.0.0", port=5000)
