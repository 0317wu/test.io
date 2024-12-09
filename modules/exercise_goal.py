
from linebot.models import FlexSendMessage

def show_exercise_goal(event, line_bot_api):
    flex_message = FlexSendMessage(
        alt_text="運動目標選單",
        contents={
            "type": "carousel",
            "contents": [
                create_goal_bubble("🏃‍♂️ 減脂", "減脂"),
                create_goal_bubble("🏋️‍♂️ 增肌", "增肌"),
                create_goal_bubble("🏃‍♀️ 提高心肺功能", "提高心肺功能"),
                create_goal_bubble("🔙 返回", "返回")
            ]
        }
    )
    line_bot_api.reply_message(event.reply_token, flex_message)

def create_goal_bubble(title, text):
    return {
        "type": "bubble",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "text", "text": title, "weight": "bold", "size": "lg"},
                {"type": "text", "text": f"選擇「{title}」來查看相關計劃。", "size": "sm", "color": "#555555"}
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

def show_fat_loss_plan(event, line_bot_api):
    flex_message = FlexSendMessage(
        alt_text="減脂運動計劃",
        contents={
            "type": "bubble",
            "hero": {
                "type": "image",
                "url": "https://i.imgur.com/fat_loss.jpg",
                "size": "full",
                "aspectRatio": "20:13",
                "aspectMode": "cover"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {"type": "text", "text": "🏃‍♂️ 減脂運動計劃", "weight": "bold", "size": "xl"},
                    {"type": "text", "text": "以下是針對減脂的運動計劃：", "size": "sm", "color": "#555555"},
                    {"type": "box", "layout": "vertical", "contents": [
                        create_plan_item("有氧運動", "跑步或游泳，每次30分鐘，每週3次"),
                        create_plan_item("重訓", "全身性訓練，每個動作3組，每組12次"),
                        create_plan_item("飲食管理", "低卡高蛋白飲食")
                    ]}
                ]
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {"type": "button", "style": "link", "action": {"type": "message", "label": "🔙 返回選擇", "text": "返回"}}
                ]
            }
        }
    )
    line_bot_api.reply_message(event.reply_token, flex_message)

def show_muscle_gain_plan(event, line_bot_api):
    flex_message = FlexSendMessage(
        alt_text="增肌運動計劃",
        contents={
            "type": "bubble",
            "hero": {
                "type": "image",
                "url": "https://i.imgur.com/muscle_gain.jpg",
                "size": "full",
                "aspectRatio": "20:13",
                "aspectMode": "cover"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {"type": "text", "text": "🏋️‍♂️ 增肌運動計劃", "weight": "bold", "size": "xl"},
                    {"type": "text", "text": "以下是針對增肌的運動計劃：", "size": "sm", "color": "#555555"},
                    {"type": "box", "layout": "vertical", "contents": [
                        create_plan_item("重訓", "專注於力量訓練，每個動作4組，每組10次"),
                        create_plan_item("高蛋白飲食", "增加蛋白質攝取"),
                        create_plan_item("高強度運動", "短時間高強度訓練")
                    ]}
                ]
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {"type": "button", "style": "link", "action": {"type": "message", "label": "🔙 返回選擇", "text": "返回"}}
                ]
            }
        }
    )
    line_bot_api.reply_message(event.reply_token, flex_message)

def show_cardiovascular_plan(event, line_bot_api):
    flex_message = FlexSendMessage(
        alt_text="提高心肺功能計劃",
        contents={
            "type": "bubble",
            "hero": {
                "type": "image",
                "url": "https://i.imgur.com/cardiovascular.jpg",
                "size": "full",
                "aspectRatio": "20:13",
                "aspectMode": "cover"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {"type": "text", "text": "🏃‍♀️ 提高心肺功能計劃", "weight": "bold", "size": "xl"},
                    {"type": "text", "text": "以下是針對心肺功能的運動計劃：", "size": "sm", "color": "#555555"},
                    {"type": "box", "layout": "vertical", "contents": [
                        create_plan_item("有氧運動", "跑步或騎車，每次30分鐘，每週3次"),
                        create_plan_item("游泳", "增強耐力，每次45分鐘，每週2次"),
                        create_plan_item("交替運動", "強度不一的運動組合")
                    ]}
                ]
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {"type": "button", "style": "link", "action": {"type": "message", "label": "🔙 返回選擇", "text": "返回"}}
                ]
            }
        }
    )
    line_bot_api.reply_message(event.reply_token, flex_message)

def create_plan_item(title, description):
    return {
        "type": "box",
        "layout": "horizontal",
        "contents": [
            {"type": "text", "text": "• " + title, "size": "sm", "color": "#555555", "flex": 1},
            {"type": "text", "text": description, "size": "sm", "color": "#111111", "flex": 5}
        ]
    }
