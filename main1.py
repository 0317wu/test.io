from linebot import LineBotApi, WebhookHandler
from linebot.models import FlexSendMessage, TextSendMessage
from flask import Flask, request, abort
import os
from dotenv import load_dotenv
from linebot.models import MessageEvent, TextMessage
import webbrowser
from diet import generate_daily_menu,generate_menu,calculate_bmi

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
                                {"type": "button", "style": "primary", "action": {"type": "message", "label": "高級者", "text": "高級者"}},
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
    elif user_message.startswith("飲食管理"):
        try:
            # 假設用戶輸入格式: 飲食管理 70 1.75（體重、身高）
            _, weight, height = user_message.split()
            weight = float(weight)
            height = float(height)
            
            # 計算 BMI
            bmi = calculate_bmi(weight, height)
            category, daily_menu = generate_daily_menu(bmi)
            
            # 構造回應消息
            menu_text = f"您的 BMI 為 {bmi:.2f}，屬於 {category}。\n\n建議菜單如下：\n"
            for meal, menu_item in daily_menu.items():
                menu_text += f"{meal}: {menu_item}\n"

            # 回應用戶
            reply_message = TextSendMessage(text=menu_text)
            line_bot_api.reply_message(event.reply_token, reply_message)

        except Exception as e:
            # 處理格式錯誤或其他問題
            error_message = TextSendMessage(text="請按照正確格式輸入：                飲食管理 體重(公斤) 身高(公尺)")
            line_bot_api.reply_message(event.reply_token, error_message)
    else:
        # 回傳預設訊息
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="請點選有效指令！"))


if __name__ == "__main__":
    app.run(port=5000)
