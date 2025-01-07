from flask import url_for
from linebot.models import FlexSendMessage

def create_plan_item(title, description, url):
    return {
        "type": "box",
        "layout": "vertical",
        "spacing": "sm",
        "contents": [
            {
                "type": "text",
                "text": "• " + title,
                "size": "sm",
                "color": "#555555",
                "wrap": True
            },
            {
                "type": "text",
                "text": description,
                "size": "xs",
                "color": "#999999",
                "wrap": True
            },
            {
                "type": "button",
                "style": "link",
                "action": {
                    "type": "uri",
                    "label": "查看影片",
                    "uri": url
                }
            }
        ]
    }



def show_exercise_guidance(event, line_bot_api):
    flex_message = FlexSendMessage(
        alt_text="運動指導選單",
        contents={
            "type": "carousel",
            "contents": [
                
                create_guidance_bubble("📋 運動指導", "運動指導"),
            ]
        }
    )
    line_bot_api.reply_message(event.reply_token, flex_message)

def create_guidance_bubble(title, text):
    return {
        "type": "bubble",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "text", "text": title, "weight": "bold", "size": "lg"},
                {"type": "text", "text": f"選擇「{title}」來查看相關內容。", "size": "sm", "color": "#555555"}
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
                    "action": {"type": "message", "label": "查看內容", "text": text}
                }
            ]
        }
    }



def show_training_plan_menu(event, line_bot_api):
    flex_message = FlexSendMessage(
        alt_text="運動指導計劃選單",
        contents={
            "type": "carousel",
            "contents": [
                create_level_bubble("👶 初學者", "初學者運動指導計劃"),
                create_level_bubble("💪 中級者", "中級者運動指導計劃"),
                create_level_bubble("🔥 高級者", "高級者運動指導計劃"),
            ]
        }
    )
    line_bot_api.reply_message(event.reply_token, flex_message)

def create_level_bubble(title, text):
    return {
        "type": "bubble",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "text", "text": title, "weight": "bold", "size": "lg"},
                {"type": "text", "text": f"選擇「{title}」來查看運動指導計劃。", "size": "sm", "color": "#555555"}
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
                    "action": {"type": "message", "label": "查看計劃", "text": text}
                }
            ]
        }
    }

def show_beginner_training_plan(event, line_bot_api):
    image_url = url_for('serve_image', filename='beginner.jpeg', _external=True, _scheme='https')
    flex_message = FlexSendMessage(
        alt_text="初學者運動指導計劃",
        contents={
            "type": "bubble",
            "hero": {
                "type": "image",
                "url": image_url,
                "size": "full",
                "aspectRatio": "20:13",
                "aspectMode": "cover",
                "action": {"type": "uri", "uri": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",
                "contents": [
                    {"type": "text", "text": "👶 初學者運動指導計劃", "weight": "bold", "size": "xl"},
                    {"type": "text", "text": "逐步建立基礎，啟動您的健身之旅。", "size": "sm", "color": "#555555"},
                    {
                        "type": "box",
                        "layout": "vertical",
                        "margin": "lg",
                        "spacing": "sm",
                        "contents": [
                            create_plan_item("基礎有氧", "快走或輕鬆跑步，每次30分鐘，每週3次", "https://www.youtube.com/watch?v=gC_L9qAHVJ8"),
                            create_plan_item("基礎重訓", "深蹲與伏地挺身，每個動作3組，每組12次", "https://www.youtube.com/watch?v=IODxDxX7oi4"),
                            create_plan_item("柔軟性運動指導", "全身拉伸，每次10分鐘", "https://www.youtube.com/watch?v=jeNwE4VXqgs")
                        ]
                    }
                ]
            }
        }
    )
    line_bot_api.reply_message(event.reply_token, flex_message)
def show_intermediate_training_plan(event, line_bot_api):
    image_url = url_for('serve_image', filename='Intermediate.jpeg', _external=True, _scheme='https')
    flex_message = FlexSendMessage(
        alt_text="中級者運動指導計劃",
        contents={
            "type": "bubble",
            "hero": {
                "type": "image",
                "url": image_url,
                "size": "full",
                "aspectRatio": "20:13",
                "aspectMode": "cover",
                "action": {"type": "uri", "uri": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",
                "contents": [
                    {"type": "text", "text": "💪 中級者運動指導計劃", "weight": "bold", "size": "xl"},
                    {"type": "text", "text": "提升您的健身水平，挑戰更高強度。", "size": "sm", "color": "#555555"},
                    {
                        "type": "box",
                        "layout": "vertical",
                        "margin": "lg",
                        "spacing": "sm",
                        "contents": [
                            create_plan_item("增強有氧運動", "跑步、騎車，每次45分鐘，每週4次", "https://www.youtube.com/watch?v=tkkMIOtKYwU"),
                            create_plan_item("增強重訓", "加入啞鈴或槓鈴訓練，每個動作4組，每組10次", "https://www.youtube.com/watch?v=U3HlEF_E9fo"),
                            create_plan_item("核心訓練", "仰臥起坐、平板支撐，每個動作3組，每組15次", "https://www.youtube.com/watch?v=DHD1-2P94DI")
                        ]
                    }
                ]
            }
        }
    )
    line_bot_api.reply_message(event.reply_token, flex_message)

def show_advanced_training_plan(event, line_bot_api):
    image_url = url_for('serve_image', filename='senior.jpeg', _external=True, _scheme='https')
    flex_message = FlexSendMessage(
        alt_text="高級者運動指導計劃",
        contents={
            "type": "bubble",
            "hero": {
                "type": "image",
                "url": image_url,
                "size": "full",
                "aspectRatio": "20:13",
                "aspectMode": "cover",
                "action": {"type": "uri", "uri": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",
                "contents": [
                    {"type": "text", "text": "🔥 高級者運動指導計劃", "weight": "bold", "size": "xl"},
                    {"type": "text", "text": "挑戰自我，達到最佳狀態。", "size": "sm", "color": "#555555"},
                    {
                        "type": "box",
                        "layout": "vertical",
                        "margin": "lg",
                        "spacing": "sm",
                        "contents": [
                            create_plan_item("高強度有氧運動", "間歇性衝刺訓練，每次60分鐘，每週5次", "https://www.youtube.com/watch?v=ml6cT4AZdqI"),
                            create_plan_item("高強度重訓", "複合動作與循環訓練，每個動作5組，每組8次", "https://www.youtube.com/watch?v=1fO1IMlkyCE"),
                            create_plan_item("高級核心訓練", "俄羅斯轉體、懸空腿舉，每個動作4組，每組20次", "https://www.youtube.com/watch?v=9VsDP584zyQ")
                        ]
                    }
                ]
            }
        }
    )
    line_bot_api.reply_message(event.reply_token, flex_message)

