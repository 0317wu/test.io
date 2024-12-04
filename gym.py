import os
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, 
    QuickReply, QuickReplyButton, MessageAction
)
from dotenv import load_dotenv

# 模擬模組（因為原始碼中這些模組是空的）
class WorkoutTracking:
    @staticmethod
    def start_workout_record(user_id):
        return TextSendMessage(text="請輸入運動類型、時間和消耗卡路里\n格式：運動,時間,卡路里 例如：跑步,45,350")
    
    @staticmethod
    def generate_workout_report(user_id):
        return TextSendMessage(text="本週運動報告\n總運動時間：120分鐘\n消耗卡路里：700卡")

class GoalManagement:
    @staticmethod
    def set_fitness_goal(user_id):
        return TextSendMessage(text="請選擇目標類型：\n1. 減重\n2. 增肌\n3. 塑形\n請回覆數字")

class WorkoutRecommendation:
    @staticmethod
    def get_workout_suggestion(user_id):
        return TextSendMessage(text="今日推薦運動：\nHIIT訓練\n時長：30分鐘\n預計消耗：400卡路里")

# 載入環境變數
load_dotenv()

# LINE Bot 配置
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET')

app = Flask(__name__)
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# 主菜单快速回复按钮
def get_main_menu_quick_reply():
    return QuickReply(items=[
        QuickReplyButton(action=MessageAction(label='记录运动', text='记录运动')),
        QuickReplyButton(action=MessageAction(label='设定目标', text='设定目标')),
        QuickReplyButton(action=MessageAction(label='运动建议', text='运动建议')),
        QuickReplyButton(action=MessageAction(label='查看报告', text='查看报告'))
    ])

@app.route("/webhook", methods=['POST'])
def webhook():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    message_text = event.message.text.strip()

    # 根据用户消息分发处理
    if message_text in ['开始', '菜单']:
        reply_message = TextSendMessage(
            text='欢迎使用健身小助手！请选择功能：',
            quick_reply=get_main_menu_quick_reply()
        )
    
    elif message_text == '记录运动':
        # 记录运动逻辑
        reply_message = WorkoutTracking.start_workout_record(user_id)
    
    elif message_text == '设定目标':
        # 目标设定逻辑
        reply_message = GoalManagement.set_fitness_goal(user_id)
    
    elif message_text == '运动建议':
        # 运动建议逻辑
        reply_message = WorkoutRecommendation.get_workout_suggestion(user_id)
    
    elif message_text == '查看报告':
        # 生成运动报告
        reply_message = WorkoutTracking.generate_workout_report(user_id)
    
    else:
        # 处理其他消息
        reply_message = TextSendMessage(
            text='我没有理解您的指令，请重新选择。',
            quick_reply=get_main_menu_quick_reply()
        )
        git commit -m "Add new files and updates"
    # 发送回复消息
    line_bot_api.reply_message(event.reply_token, reply_message)

if __name__ == "__main__":
    # 注意：實際部署時需要使用 webhook
    app.run(debug=True, port=5000)