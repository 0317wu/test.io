from flask import url_for
from linebot.models import FlexSendMessage

def create_plan_item(title, description):
    return {
        "type": "box",
        "layout": "horizontal",
        "spacing": "sm",
        "contents": [
            {
                "type": "text",
                "text": "• " + title,
                "size": "sm",
                "color": "#555555",
                "flex": 1,
                "wrap": True
            },
            {
                "type": "text",
                "text": description,
                "size": "sm",
                "color": "#111111",
                "flex": 5,
                "wrap": True
            }
        ]
    }

def show_exercise_guidance(event, line_bot_api):
    flex_message = FlexSendMessage(
        alt_text="運動指導選單",
        contents={
            "type": "carousel",
            "contents": [
                create_guidance_bubble("🍎 飲食指導", "飲食指導"),
                create_guidance_bubble("📋 訓練計劃", "訓練計劃"),
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

def show_diet_guidance_menu(event, line_bot_api):
    flex_message = FlexSendMessage(
        alt_text="飲食指導選單",
        contents={
            "type": "carousel",
            "contents": [
                create_diet_bubble("👶 初階者飲食方案", "初階者飲食方案"),
                create_diet_bubble("💪 中級者飲食方案", "中級者飲食方案"),
                create_diet_bubble("🔥 高級者飲食方案", "高級者飲食方案"),
            ]
        }
    )
    line_bot_api.reply_message(event.reply_token, flex_message)

def create_diet_bubble(title, text):
    return {
        "type": "bubble",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "text", "text": title, "weight": "bold", "size": "lg"},
                {"type": "text", "text": f"選擇「{title}」來查看飲食方案。", "size": "sm", "color": "#555555"}
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
                    "action": {"type": "message", "label": "查看方案", "text": text}
                }
            ]
        }
    }

def show_beginner_diet_plan(event, line_bot_api):
    image_url = url_for('serve_image', filename='beginner_diet.jpeg', _external=True, _scheme='https')
    flex_message = FlexSendMessage(
        alt_text="👶 初階者飲食方案",
        contents={
            "type": "bubble",
            "hero": {
                "type": "image",
                "url": image_url,
                "size": "full",
                "aspectRatio": "20:13",
                "aspectMode": "cover"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",
                "contents": [
                    {"type": "text", "text": "👶 初階者飲食方案", "weight": "bold", "size": "xl"},
                    {"type": "text", "text": "開始您的健身之旅，以下是適合初階者的飲食建議：", "size": "sm", "color": "#555555"},
                    {
                        "type": "box",
                        "layout": "vertical",
                        "margin": "lg",
                        "spacing": "sm",
                        "contents": [
                            create_plan_item("高蛋白攝取", "增加雞胸肉、魚類、豆類等蛋白質來源。"),
                            create_plan_item("控制總熱量", "保持每日熱量攝取略低於維持熱量。"),
                            create_plan_item("多吃蔬菜", "確保每餐包含豐富的蔬菜。")
                        ]
                    }
                ]
            }
        }
    )
    line_bot_api.reply_message(event.reply_token, flex_message)

def show_intermediate_diet_plan(event, line_bot_api):
    image_url = url_for('serve_image', filename='Intermediate_diet.jpeg', _external=True, _scheme='https')
    flex_message = FlexSendMessage(
        alt_text="💪 中級者飲食方案",
        contents={
            "type": "bubble",
            "hero": {
                "type": "image",
                "url": image_url,
                "size": "full",
                "aspectRatio": "20:13",
                "aspectMode": "cover"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",
                "contents": [
                    {"type": "text", "text": "💪 中級者飲食方案", "weight": "bold", "size": "xl"},
                    {"type": "text", "text": "提升您的飲食管理，以下是適合中級者的飲食建議：", "size": "sm", "color": "#555555"},
                    {
                        "type": "box",
                        "layout": "vertical",
                        "margin": "lg",
                        "spacing": "sm",
                        "contents": [
                            create_plan_item("高質量蛋白質", "如牛肉、雞胸肉、魚類等。"),
                            create_plan_item("複合碳水化合物", "如糙米、燕麥、全麥麵包。"),
                            create_plan_item("健康脂肪", "如橄欖油、堅果、酪梨。")
                        ]
                    }
                ]
            }
        }
    )
    line_bot_api.reply_message(event.reply_token, flex_message)

def show_advanced_diet_plan(event, line_bot_api):
    image_url = url_for('serve_image', filename='senior_diet.jpeg', _external=True, _scheme='https')
    flex_message = FlexSendMessage(
        alt_text="🔥 高級者飲食方案",
        contents={
            "type": "bubble",
            "hero": {
                "type": "image",
                "url": image_url,
                "size": "full",
                "aspectRatio": "20:13",
                "aspectMode": "cover"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",
                "contents": [
                    {"type": "text", "text": "🔥 高級者飲食方案", "weight": "bold", "size": "xl"},
                    {"type": "text", "text": "達到最佳健身狀態，以下是適合高級者的飲食建議：", "size": "sm", "color": "#555555"},
                    {
                        "type": "box",
                        "layout": "vertical",
                        "margin": "lg",
                        "spacing": "sm",
                        "contents": [
                            create_plan_item("精確熱量控制", "根據目標調整每日熱量攝取。"),
                            create_plan_item("微量營養素補充", "如維生素、礦物質補充劑。"),
                            create_plan_item("飲食時機安排", "如訓練前後的營養補充。")
                        ]
                    }
                ]
            }
        }
    )
    line_bot_api.reply_message(event.reply_token, flex_message)

def show_training_plan_menu(event, line_bot_api):
    flex_message = FlexSendMessage(
        alt_text="訓練計劃選單",
        contents={
            "type": "carousel",
            "contents": [
                create_level_bubble("👶 初學者", "初學者訓練計劃"),
                create_level_bubble("💪 中級者", "中級者訓練計劃"),
                create_level_bubble("🔥 高級者", "高級者訓練計劃"),
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
                {"type": "text", "text": f"選擇「{title}」來查看訓練計劃。", "size": "sm", "color": "#555555"}
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
        alt_text="初學者訓練計劃",
        contents={
            "type": "bubble",
            "hero": {
                "type": "image",
                "url": image_url,
                "size": "full",
                "aspectRatio": "20:13",
                "aspectMode": "cover",
                "action": {"type": "uri", "uri": "https://yourwebsite.com/beginner-plan"}
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",
                "contents": [
                    {"type": "text", "text": "👶 初學者訓練計劃", "weight": "bold", "size": "xl"},
                    {"type": "text", "text": "逐步建立基礎，啟動您的健身之旅。", "size": "sm", "color": "#555555"},
                    {
                        "type": "box",
                        "layout": "vertical",
                        "margin": "lg",
                        "spacing": "sm",
                        "contents": [
                            create_plan_item("基礎有氧", "快走或輕鬆跑步，每次30分鐘，每週3次"),
                            create_plan_item("基礎重訓", "深蹲與伏地挺身，每個動作3組，每組12次"),
                            create_plan_item("柔軟性訓練", "全身拉伸，每次10分鐘")
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
        alt_text="中級者訓練計劃",
        contents={
            "type": "bubble",
            "hero": {
                "type": "image",
                "url": image_url,
                "size": "full",
                "aspectRatio": "20:13",
                "aspectMode": "cover",
                "action": {"type": "uri", "uri": "https://yourwebsite.com/intermediate-plan"}
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",
                "contents": [
                    {"type": "text", "text": "💪 中級者訓練計劃", "weight": "bold", "size": "xl"},
                    {"type": "text", "text": "提升您的健身水平，挑戰更高強度。", "size": "sm", "color": "#555555"},
                    {
                        "type": "box",
                        "layout": "vertical",
                        "margin": "lg",
                        "spacing": "sm",
                        "contents": [
                            create_plan_item("增強有氧運動", "跑步、騎車，每次45分鐘，每週4次"),
                            create_plan_item("增強重訓", "加入啞鈴或槓鈴訓練，每個動作4組，每組10次"),
                            create_plan_item("核心訓練", "仰臥起坐、平板支撐，每個動作3組，每組15次")
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
        alt_text="高級者訓練計劃",
        contents={
            "type": "bubble",
            "hero": {
                "type": "image",
                "url": image_url,
                "size": "full",
                "aspectRatio": "20:13",
                "aspectMode": "cover",
                "action": {"type": "uri", "uri": "https://yourwebsite.com/advanced-plan"}
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",
                "contents": [
                    {"type": "text", "text": "🔥 高級者訓練計劃", "weight": "bold", "size": "xl"},
                    {"type": "text", "text": "挑戰自我，達到最佳狀態。", "size": "sm", "color": "#555555"},
                    {
                        "type": "box",
                        "layout": "vertical",
                        "margin": "lg",
                        "spacing": "sm",
                        "contents": [
                            create_plan_item("高強度有氧運動", "間歇性衝刺訓練，每次60分鐘，每週5次"),
                            create_plan_item("高強度重訓", "複合動作與循環訓練，每個動作5組，每組8次"),
                            create_plan_item("高級核心訓練", "俄羅斯轉體、懸空腿舉，每個動作4組，每組20次")
                        ]
                    }
                ]
            }
        }
    )
    line_bot_api.reply_message(event.reply_token, flex_message)