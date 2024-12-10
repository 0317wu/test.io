import os
import sqlite3
from datetime import datetime
from linebot import LineBotApi, WebhookHandler
from linebot.models import (
    FlexSendMessage,
    TextSendMessage,
    LocationMessage,
    MessageEvent,
    TextMessage,
    FollowEvent,
    TemplateSendMessage,
    ButtonsTemplate,
    URIAction
)
from flask import Flask, request, abort
from dotenv import load_dotenv
import random

# 載入環境變數
load_dotenv()
app = Flask(__name__)

# LINE BOT API 初始化
line_bot_api = LineBotApi(os.getenv('LINE_CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.getenv('LINE_CHANNEL_SECRET'))

# 用來儲存資料庫連接
DATABASE = 'user_body_data.db'

# 分頁大小
PAGE_SIZE = 10

# 創建資料庫連接的上下文管理器
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # 這樣就可以用字典形式來操作資料
    return conn

# 初始化資料庫，創建表格
def init_db():
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS body_data (
                        user_id TEXT,
                        weight REAL,
                        height REAL,
                        bmi REAL,
                        time TEXT)''')
        conn.commit()

# 初始化資料庫
init_db()

# 用於追蹤使用者狀態（例如等待輸入體態紀錄或瀏覽頁面）
user_states = {}
def calculate_bmi(weight, height_cm):
    height_m = height_cm / 100
    bmi = weight / (height_m ** 2)
    return bmi

def recommend_daily_menu(bmi):
    menus = {
        "underweight": {
            "breakfast": [
                "香蕉牛奶燕麥片 + 水煮蛋 + 香蕉",
                "全麥吐司 + 花生醬 + 牛奶",
                "豆漿 + 蔬菜三明治",
                "水果沙拉 + 燕麥餅乾",
                "雞蛋蔬菜煎餅 + 豆漿",
                "藍莓優格杯 + 堅果",
                "牛奶煎餅 + 蜂蜜",
                "水果奶昔 + 全麥麵包",
                "綜合堅果 + 水果",
                "素食漢堡 + 蔬菜汁",
                "烤地瓜 + 酸奶",
                "菠菜芝士歐姆蛋 + 全麥吐司",
                "鳳梨糙米粥 + 水果",
                "豆腐蔬菜湯 + 全麥饅頭",
                "蜂蜜核桃麥片 + 牛奶",
                "番茄炒蛋 + 全麥吐司",
                "水果優格沙拉 + 燕麥餅乾",
                "牛油果吐司 + 水煮蛋",
                "香菇豆腐粥 + 水果",
                "玉米片 + 低脂牛奶 + 水果"
            ],
            "lunch": [
                "雞胸肉炒飯 + 水煮青菜 + 雞湯",
                "牛肉麵 + 青菜 + 豆腐",
                "三文魚便當 + 蔬菜沙拉",
                "雞肉蔬菜捲 + 糙米飯",
                "豬里脊炒蔬菜 + 米飯",
                "蝦仁炒麵 + 青菜湯",
                "烤鴨腿 + 地瓜 + 蔬菜",
                "素食披薩 + 混合沙拉",
                "牛肉壽喜燒 + 白飯",
                "鯖魚定食 + 味噌湯",
                "火雞肉三明治 + 蔬菜湯",
                "蒜蓉蒸蝦 + 糙米飯 + 青菜",
                "豆腐蔬菜燴飯 + 湯",
                "羊肉串 + 烤蔬菜 + 全麥麵包",
                "泰式炒河粉 + 涼拌木瓜",
                "豬腳飯 + 蔬菜",
                "素食壽司 + 味噌湯",
                "牛肉炒西蘭花 + 米飯",
                "雞肉咖哩 + 藜麥",
                "鯛魚燉豆腐 + 紫米飯"
            ],
            "dinner": [
                "義大利麵 + 魚排 + 番茄濃湯",
                "烤雞腿 + 馬鈴薯泥 + 蔬菜沙拉",
                "牛肉燉蔬菜 + 全麥麵包",
                "豆腐炒青菜 + 紫米飯",
                "泰式炒河粉 + 涼拌青木瓜",
                "燉羊肉 + 蔬菜 + 全麥飯",
                "海鮮燴飯 + 蔬菜湯",
                "素食咖哩 + 藜麥",
                "蒸豆魚 + 青菜 + 糙米飯",
                "烤蔬菜拼盤 + 雞肉串",
                "烤鮭魚 + 蔬菜沙拉",
                "瘦牛肉炒西蘭花 + 藜麥",
                "番茄豆腐湯 + 全麥吐司",
                "燉雞肉 + 藜麥沙拉",
                "素食焗飯 + 混合蔬菜",
                "烤羊排 + 地瓜泥 + 青菜",
                "蒸鱈魚 + 蔬菜 + 紫米飯",
                "蔬菜豆腐鍋 + 全麥飯",
                "牛肉燉蘑菇 + 全麥麵包",
                "烤鴨腿 + 地瓜泥 + 蔬菜"
            ],
            "snack": [
               "花生醬吐司 + 杏仁牛奶",
                "優格 + 堅果",
                "水果優格冰沙",
                "蔬菜棒配鷹嘴豆泥",
                "全麥餅乾 + 水果",
                "香蕉奶昔",
                "低脂起司片 + 蘋果",
                "能量棒",
                "堅果混合",
                "胡蘿蔔條 + 低脂酸奶",
                "水果乾 + 無糖優格",
                "藍莓奶昔",
                "燕麥能量球",
                "蔬菜沙拉 + 鷹嘴豆",
                "小份量低脂冰淇淋",
                "番茄片 + 低脂起司",
                "低糖果凍",
                "椰子水 + 堅果",
                "低脂奶酪 + 水果片",
                "葡萄乾 + 無糖豆奶"
            ]
        
        },
        "normal": {
            "breakfast": [
                "全麥吐司 + 蔬菜沙拉 + 水煮蛋",
                "燕麥片 + 藍莓 + 牛奶",
                "水果優格碗 + 燕麥",
                "蔬菜蛋白奶昔",
                "雞蛋蔬菜煎餅 + 果汁",
                "綜合水果盤 + 堅果",
                "低脂牛奶 + 全麥麵包",
                "豆漿 + 燕麥粥",
                "水果沙拉 + 燕麥餅",
                "素食漢堡 + 蔬菜汁",
                "牛油果吐司 + 水煮蛋",
                "菠菜芝士歐姆蛋 + 全麥吐司",
                "鳳梨糙米粥 + 水果",
                "豆腐蔬菜湯 + 全麥饅頭",
                "蜂蜜核桃麥片 + 牛奶",
                "番茄炒蛋 + 全麥吐司",
                "水果優格沙拉 + 燕麥餅乾",
                "香菇豆腐粥 + 水果",
                "玉米片 + 低脂牛奶 + 水果",
                "牛奶煎餅 + 蜂蜜"
            ],
            "lunch": [
                  "燒烤雞胸肉 + 糙米飯 + 烤蔬菜",
                "蒸魚 + 地瓜 + 時令蔬菜湯",
                "雞肉凱薩沙拉 + 全麥麵包",
                "牛肉蔬菜炒麵 + 湯",
                "豆腐炒飯 + 青菜",
                "鮮蝦沙拉 + 全麥吐司",
                "火雞三明治 + 蔬菜湯",
                "素食壽司 + 味噌湯",
                "牛肉燉飯 + 青豆",
                "烤鴨肉 + 紫薯 + 蔬菜",
                "番茄牛肉燉飯 + 蔬菜",
                "烤雞肉捲 + 混合沙拉",
                "蔬菜炒麵 + 海鮮湯",
                "豆腐海鮮燴飯 + 湯",
                "羊肉炒蔬菜 + 全麥飯",
                "泰式牛肉沙拉 + 藜麥",
                "香煎鯖魚 + 糙米飯 + 青菜",
                "素食披薩 + 混合沙拉",
                "雞肉菠菜義大利麵 + 蔬菜湯",
                "鯛魚定食 + 味噌湯"
            ],
            "dinner": [
                "蒸魚 + 地瓜 + 時令蔬菜湯",
                "烤雞胸肉 + 蔬菜沙拉 + 糙米飯",
                "蔬菜豆腐鍋 + 全麥飯",
                "瘦肉燉菜 + 藜麥",
                "泰式綠咖哩 + 藜麥",
                "烤鮭魚 + 蔬菜拼盤",
                "素食披薩 + 混合沙拉",
                "牛肉燉蘑菇 + 全麥麵包",
                "烤鴨腿 + 地瓜泥",
                "豆腐煲 + 藜麥飯",
                "番茄牛肉燉飯 + 蔬菜",
                "香煎鯖魚 + 藜麥沙拉",
                "雞肉菠菜義大利麵 + 蔬菜湯",
                "素食咖哩 + 全麥飯",
                "烤羊排 + 地瓜泥 + 青菜",
                "蒸鱈魚 + 蔬菜 + 紫米飯",
                "豆腐蔬菜燴飯 + 藜麥",
                "牛肉炒西蘭花 + 藜麥",
                "燉雞肉 + 藜麥沙拉",
                "蔬菜焗飯 + 混合蔬菜"
            ],
            "snack": [
                "優格 + 堅果",
                "水果沙拉 + 低脂優格",
                "蔬菜棒配鷹嘴豆泥",
                "全麥餅乾 + 水果",
                "低脂起司 + 蘋果片",
                "胡蘿蔔條 + 低脂酸奶",
                "香蕉奶昔",
                "能量棒",
                "堅果混合",
                "水果優格冰沙",
                "藍莓奶昔",
                "燕麥能量球",
                "蔬菜沙拉 + 鷹嘴豆",
                "小份量低脂冰淇淋",
                "番茄片 + 低脂起司",
                "低糖果凍",
                "椰子水 + 堅果",
                "低脂奶酪 + 水果片",
                "葡萄乾 + 無糖優格",
                "水果乾 + 無糖豆奶"
            ]
        
        },
        "overweight": {
            "早餐": [
                "低脂優格 + 蘋果片 + 水煮蛋",
                "全麥吐司 + 牛油果 + 水煮蛋",
                "蔬菜燕麥粥 + 堅果",
                "水果奶昔 + 全麥餅乾",
                "雞蛋蔬菜煎餅 + 豆漿",
                "藍莓優格杯 + 堅果",
                "牛奶煎餅 + 蜂蜜",
                "水果沙拉 + 燕麥餅",
                "素食漢堡 + 蔬菜汁",
                "綜合堅果 + 水果",
                "菠菜芝士歐姆蛋 + 全麥吐司",
                "鳳梨糙米粥 + 水果",
                "豆腐蔬菜湯 + 全麥饅頭",
                "蜂蜜核桃麥片 + 牛奶",
                "番茄炒蛋 + 全麥吐司",
                "水果優格沙拉 + 燕麥餅乾",
                "香菇豆腐粥 + 水果",
                "玉米片 + 低脂牛奶 + 水果",
                "牛油果吐司 + 水煮蛋",
                "牛奶煎餅 + 蜂蜜"
            ],
            "午餐": [
                "烤雞胸肉 + 蔬菜沙拉 + 糙米飯",
                "蒸魚 + 地瓜 + 時令蔬菜湯",
                "豆腐蔬菜炒飯 + 湯",
                "瘦牛肉沙拉 + 全麥麵包",
                "火雞肉捲 + 混合沙拉",
                "鮮蝦炒麵 + 青菜",
                "烤鴨腿 + 紫薯 + 蔬菜",
                "素食壽司 + 味噌湯",
                "牛肉燉飯 + 青豆",
                "豆腐炒青菜 + 紫米飯",
                "番茄牛肉燉飯 + 蔬菜",
                "烤雞肉捲 + 混合沙拉",
                "蔬菜炒麵 + 海鮮湯",
                "豆腐海鮮燴飯 + 湯",
                "羊肉炒蔬菜 + 全麥飯",
                "泰式牛肉沙拉 + 藜麥",
                "香煎鯖魚 + 糙米飯 + 青菜",
                "素食披薩 + 混合沙拉",
                "雞肉菠菜義大利麵 + 蔬菜湯",
                "鯛魚定食 + 味噌湯"
            ],
            "晚餐": [
                "蒸魚 + 地瓜 + 時令蔬菜湯",
                "烤雞胸肉 + 蔬菜沙拉 + 糙米飯",
                "蔬菜豆腐鍋 + 藜麥",
                "瘦肉燉菜 + 全麥飯",
                "泰式綠咖哩 + 藜麥",
                "烤鮭魚 + 蔬菜拼盤",
                "素食披薩 + 混合沙拉",
                "牛肉燉蘑菇 + 全麥麵包",
                "烤鴨腿 + 地瓜泥",
                "豆腐煲 + 藜麥飯",
                "番茄牛肉燉飯 + 蔬菜",
                "香煎鯖魚 + 藜麥沙拉",
                "雞肉菠菜義大利麵 + 蔬菜湯",
                "素食咖哩 + 全麥飯",
                "烤羊排 + 地瓜泥 + 青菜",
                "蒸鱈魚 + 蔬菜 + 紫米飯",
                "豆腐蔬菜燴飯 + 藜麥",
                "牛肉炒西蘭花 + 藜麥",
                "燉雞肉 + 藜麥沙拉",
                "蔬菜焗飯 + 混合蔬菜"
            ],
            "加餐": [
                "優格 + 堅果",
                "水果沙拉 + 低脂優格",
                "蔬菜棒配鷹嘴豆泥",
                "全麥餅乾 + 水果",
                "低脂起司 + 蘋果片",
                "胡蘿蔔條 + 低脂酸奶",
                "香蕉奶昔",
                "能量棒",
                "堅果混合",
                "水果優格冰沙",
                "藍莓奶昔",
                "燕麥能量球",
                "蔬菜沙拉 + 鷹嘴豆",
                "小份量低脂冰淇淋",
                "番茄片 + 低脂起司",
                "低糖果凍",
                "椰子水 + 堅果",
                "低脂奶酪 + 水果片",
                "葡萄乾 + 無糖優格",
                "水果乾 + 無糖豆奶"
            ]
        },
        "obese": {
              "早餐": [
                "低脂優格 + 蘋果片 + 水煮蛋",
                "全麥吐司 + 牛油果 + 水煮蛋",
                "蔬菜燕麥粥 + 堅果",
                "水果奶昔 + 全麥餅乾",
                "雞蛋蔬菜煎餅 + 豆漿",
                "藍莓優格杯 + 堅果",
                "牛奶煎餅 + 蜂蜜",
                "水果沙拉 + 燕麥餅",
                "素食漢堡 + 蔬菜汁",
                "綜合堅果 + 水果",
                "菠菜芝士歐姆蛋 + 全麥吐司",
                "鳳梨糙米粥 + 水果",
                "豆腐蔬菜湯 + 全麥饅頭",
                "蜂蜜核桃麥片 + 牛奶",
                "番茄炒蛋 + 全麥吐司",
                "水果優格沙拉 + 燕麥餅乾",
                "香菇豆腐粥 + 水果",
                "玉米片 + 低脂牛奶 + 水果",
                "牛油果吐司 + 水煮蛋",
                "牛奶煎餅 + 蜂蜜"
            ],
            "午餐": [
                "烤雞胸肉 + 蔬菜沙拉 + 糙米飯",
                "蒸魚 + 地瓜 + 時令蔬菜湯",
                "豆腐蔬菜炒飯 + 湯",
                "瘦牛肉沙拉 + 全麥麵包",
                "火雞肉捲 + 混合沙拉",
                "鮮蝦炒麵 + 青菜",
                "烤鴨腿 + 紫薯 + 蔬菜",
                "素食壽司 + 味噌湯",
                "牛肉燉飯 + 青豆",
                "豆腐炒青菜 + 紫米飯",
                "番茄牛肉燉飯 + 蔬菜",
                "烤雞肉捲 + 混合沙拉",
                "蔬菜炒麵 + 海鮮湯",
                "豆腐海鮮燴飯 + 湯",
                "羊肉炒蔬菜 + 全麥飯",
                "泰式牛肉沙拉 + 藜麥",
                "香煎鯖魚 + 糙米飯 + 青菜",
                "素食披薩 + 混合沙拉",
                "雞肉菠菜義大利麵 + 蔬菜湯",
                "鯛魚定食 + 味噌湯"
            ],
            "晚餐": [
                "蒸魚 + 地瓜 + 時令蔬菜湯",
                "烤雞胸肉 + 蔬菜沙拉 + 糙米飯",
                "蔬菜豆腐鍋 + 藜麥",
                "瘦肉燉菜 + 全麥飯",
                "泰式綠咖哩 + 藜麥",
                "烤鮭魚 + 蔬菜拼盤",
                "素食披薩 + 混合沙拉",
                "牛肉燉蘑菇 + 全麥麵包",
                "烤鴨腿 + 地瓜泥",
                "豆腐煲 + 藜麥飯",
                "番茄牛肉燉飯 + 蔬菜",
                "香煎鯖魚 + 藜麥沙拉",
                "雞肉菠菜義大利麵 + 蔬菜湯",
                "素食咖哩 + 全麥飯",
                "烤羊排 + 地瓜泥 + 青菜",
                "蒸鱈魚 + 蔬菜 + 紫米飯",
                "豆腐蔬菜燴飯 + 藜麥",
                "牛肉炒西蘭花 + 藜麥",
                "燉雞肉 + 藜麥沙拉",
                "蔬菜焗飯 + 混合蔬菜"
            ],
            "加餐": [
                "優格 + 堅果",
                "水果沙拉 + 低脂優格",
                "蔬菜棒配鷹嘴豆泥",
                "全麥餅乾 + 水果",
                "低脂起司 + 蘋果片",
                "胡蘿蔔條 + 低脂酸奶",
                "香蕉奶昔",
                "能量棒",
                "堅果混合",
                "水果優格冰沙",
                "藍莓奶昔",
                "燕麥能量球",
                "蔬菜沙拉 + 鷹嘴豆",
                "小份量低脂冰淇淋",
                "番茄片 + 低脂起司",
                "低糖果凍",
                "椰子水 + 堅果",
                "低脂奶酪 + 水果片",
                "葡萄乾 + 無糖優格",
                "水果乾 + 無糖豆奶"
            ]
        }
    
    }

    if bmi < 18.5:
        category = "underweight"
    elif 18.5 <= bmi < 24:
        category = "normal"
    elif 24 <= bmi < 27:
        category = "overweight"
    else:
        category = "obese"
    
    selected_menu = {
        meal: random.choice(options)
        for meal, options in menus[category].items()
    }

    menu = (
        f"🥗 **每日菜單建議（{'體重過輕' if category == 'underweight' else '正常體重' if category == 'normal' else '過重' if category == 'overweight' else '肥胖'}）**\n"
        f"• 早餐：{selected_menu['breakfast']}\n"
        f"• 午餐：{selected_menu['lunch']}\n"
        f"• 晚餐：{selected_menu['dinner']}\n"
        f"• 點心：{selected_menu['snack']}"
    )
    return menu


@app.route("/callback", methods=['POST'])
def callback():
    # 驗證 LINE 平台的請求
    signature = request.headers.get('X-Line-Signature')
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except Exception as e:
        print(f"Error: {e}")  # 建議在生產環境中使用適當的日誌系統
        abort(400)
    return 'OK'

# 處理關注事件（首次加入機器人）
@handler.add(FollowEvent)
def handle_follow(event):
    welcome_message = (
        "🎉 歡迎使用健身助手！\n"
        "請傳送「開始」以進入主選單。"
    )
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=welcome_message))

# 顯示主選單
def show_main_menu(event):
    flex_message = FlexSendMessage(
        alt_text="開始選單",
        contents={
            "type": "bubble",
            "hero": {
                "type": "image",
                "url": "https://i.imgur.com/your_image.jpg",  # 替換為有效的圖片URL
                "size": "full",
                "aspectRatio": "20:13",
                "aspectMode": "cover",
                "action": {"type": "uri", "uri": "https://yourwebsite.com"}
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",
                "contents": [
                    {"type": "text", "text": "💪 健身助手", "weight": "bold", "size": "xl"},
                    {"type": "text", "text": "請選擇您想要的功能", "size": "sm", "color": "#555555"}
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
                        "action": {"type": "message", "label": "🏆 運動目標", "text": "運動目標"}
                    },
                    {
                        "type": "button",
                        "style": "primary",
                        "action": {"type": "message", "label": "📋 運動指導", "text": "運動指導"}
                    },
                    {
                        "type": "button",
                        "style": "primary",
                        "action": {"type": "message", "label": "🎥 運動教學", "text": "運動教學"}
                    },
                    {
                        "type": "button",
                        "style": "primary",
                        "action": {"type": "message", "label": "📊 體態紀錄", "text": "體態紀錄"}
                    },
                    {
                        "type": "button",
                        "style": "primary",
                        "action": {
                            "type": "uri",
                            "label": "📍 找附近的健身房",
                            "uri": "https://www.google.com/maps/search/?api=1&query=gym"
                        }
                    }
                ]
            }
        }
    )
    line_bot_api.reply_message(event.reply_token, flex_message)
# 顯示運動目標選單
def show_exercise_goal(event):
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

# 減脂運動計劃
def show_fat_loss_plan(event):
    flex_message = FlexSendMessage(
        alt_text="減脂運動計劃",
        contents={
            "type": "bubble",
            "hero": {
                "type": "image",
                "url": "https://i.imgur.com/fat_loss.jpg",  # 替換為有效的圖片URL
                "size": "full",
                "aspectRatio": "20:13",
                "aspectMode": "cover"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",  # 減少間距
                "contents": [
                    {"type": "text", "text": "🏃‍♂️ 減脂運動計劃", "weight": "bold", "size": "xl"},
                    {"type": "text", "text": "以下是針對減脂的運動計劃：", "size": "sm", "color": "#555555"},
                    {
                        "type": "box",
                        "layout": "vertical",
                        "margin": "lg",
                        "spacing": "sm",
                        "contents": [
                            create_plan_item("有氧運動", "跑步或游泳，每次30分鐘，每週3次"),
                            create_plan_item("重訓", "全身性訓練，每個動作3組，每組12次"),
                            create_plan_item("飲食管理", "低卡高蛋白飲食")
                        ]
                    }
                ]
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",
                "contents": [
                    {
                        "type": "button",
                        "style": "link",
                        "action": {"type": "message", "label": "🔙 返回選擇", "text": "返回"}
                    }
                ]
            }
        }
    )
    line_bot_api.reply_message(event.reply_token, flex_message)

# 增肌運動計劃
def show_muscle_gain_plan(event):
    flex_message = FlexSendMessage(
        alt_text="增肌運動計劃",
        contents={
            "type": "bubble",
            "hero": {
                "type": "image",
                "url": "https://i.imgur.com/muscle_gain.jpg",  # 替換為有效的圖片URL
                "size": "full",
                "aspectRatio": "20:13",
                "aspectMode": "cover"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",  # 減少間距
                "contents": [
                    {"type": "text", "text": "🏋️‍♂️ 增肌運動計劃", "weight": "bold", "size": "xl"},
                    {"type": "text", "text": "以下是針對增肌的運動計劃：", "size": "sm", "color": "#555555"},
                    {
                        "type": "box",
                        "layout": "vertical",
                        "margin": "lg",
                        "spacing": "sm",
                        "contents": [
                            create_plan_item("重訓", "專注於力量訓練，每個動作4組，每組10次"),
                            create_plan_item("高蛋白飲食", "增加蛋白質攝取"),
                            create_plan_item("高強度運動", "短時間高強度訓練")
                        ]
                    }
                ]
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",
                "contents": [
                    {
                        "type": "button",
                        "style": "link",
                        "action": {"type": "message", "label": "🔙 返回選擇", "text": "返回"}
                    }
                ]
            }
        }
    )
    line_bot_api.reply_message(event.reply_token, flex_message)

# 提高心肺功能計劃
def show_cardiovascular_plan(event):
    flex_message = FlexSendMessage(
        alt_text="提高心肺功能計劃",
        contents={
            "type": "bubble",
            "hero": {
                "type": "image",
                "url": "https://i.imgur.com/cardiovascular.jpg",  # 替換為有效的圖片URL
                "size": "full",
                "aspectRatio": "20:13",
                "aspectMode": "cover"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",  # 減少間距
                "contents": [
                    {"type": "text", "text": "🏃‍♀️ 提高心肺功能計劃", "weight": "bold", "size": "xl"},
                    {"type": "text", "text": "以下是針對心肺功能的運動計劃：", "size": "sm", "color": "#555555"},
                    {
                        "type": "box",
                        "layout": "vertical",
                        "margin": "lg",
                        "spacing": "sm",
                        "contents": [
                            create_plan_item("有氧運動", "跑步或騎車，每次30分鐘，每週3次"),
                            create_plan_item("游泳", "增強耐力，每次45分鐘，每週2次"),
                            create_plan_item("交替運動", "強度不一的運動組合")
                        ]
                    }
                ]
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",
                "contents": [
                    {
                        "type": "button",
                        "style": "link",
                        "action": {"type": "message", "label": "🔙 返回選擇", "text": "返回"}
                    }
                ]
            }
        }
    )
    line_bot_api.reply_message(event.reply_token, flex_message)

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
                "wrap": True  # 允許換行
            },
            {
                "type": "text",
                "text": description,
                "size": "sm",
                "color": "#111111",
                "flex": 5,
                "wrap": True  # 允許換行
            }
        ]
    }

# 顯示運動指導選單
def show_exercise_guidance(event):
    flex_message = FlexSendMessage(
        alt_text="運動指導選單",
        contents={
            "type": "carousel",
            "contents": [
                create_guidance_bubble("🍎 飲食指導", "飲食指導"),
                create_guidance_bubble("📋 訓練計劃", "訓練計劃"),
                create_guidance_bubble("🔙 返回", "返回")
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

# 顯示飲食指導選單（初階者、中級者、高級者）
def show_diet_guidance_menu(event):
    flex_message = FlexSendMessage(
        alt_text="飲食指導選單",
        contents={
            "type": "carousel",
            "contents": [
                create_diet_bubble("👶 初階者飲食方案", "初階者飲食方案"),
                create_diet_bubble("💪 中級者飲食方案", "中級者飲食方案"),
                create_diet_bubble("🔥 高級者飲食方案", "高級者飲食方案"),
                create_diet_bubble("🔙 返回", "返回")
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

# 初階者飲食方案
def show_beginner_diet_plan(event):
    flex_message = FlexSendMessage(
        alt_text="👶 初階者飲食方案",
        contents={
            "type": "bubble",
            "hero": {
                "type": "image",
                "url": "https://i.imgur.com/beginner_diet.jpg",  # 替換為有效的圖片URL
                "size": "full",
                "aspectRatio": "20:13",
                "aspectMode": "cover"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",  # 減少間距
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
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",
                "contents": [
                    {"type": "button", "style": "link", "action": {"type": "message", "label": "🔙 返回選擇", "text": "飲食指導"}}
                ]
            }
        }
    )
    line_bot_api.reply_message(event.reply_token, flex_message)

# 中級者飲食方案
def show_intermediate_diet_plan(event):
    flex_message = FlexSendMessage(
        alt_text="💪 中級者飲食方案",
        contents={
            "type": "bubble",
            "hero": {
                "type": "image",
                "url": "https://i.imgur.com/intermediate_diet.jpg",  # 替換為有效的圖片URL
                "size": "full",
                "aspectRatio": "20:13",
                "aspectMode": "cover"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",  # 減少間距
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
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",
                "contents": [
                    {"type": "button", "style": "link", "action": {"type": "message", "label": "🔙 返回選擇", "text": "飲食指導"}}
                ]
            }
        }
    )
    line_bot_api.reply_message(event.reply_token, flex_message)

# 高級者飲食方案
def show_advanced_diet_plan(event):
    flex_message = FlexSendMessage(
        alt_text="🔥 高級者飲食方案",
        contents={
            "type": "bubble",
            "hero": {
                "type": "image",
                "url": "https://i.imgur.com/advanced_diet.jpg",  # 替換為有效的圖片URL
                "size": "full",
                "aspectRatio": "20:13",
                "aspectMode": "cover"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",  # 減少間距
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
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",
                "contents": [
                    {"type": "button", "style": "link", "action": {"type": "message", "label": "🔙 返回選擇", "text": "飲食指導"}}
                ]
            }
        }
    )
    line_bot_api.reply_message(event.reply_token, flex_message)

# 顯示訓練計劃選單（初學者、中級者、高級者）
def show_training_plan_menu(event):
    flex_message = FlexSendMessage(
        alt_text="訓練計劃選單",
        contents={
            "type": "carousel",
            "contents": [
                create_level_bubble("👶 初學者", "初學者訓練計劃"),
                create_level_bubble("💪 中級者", "中級者訓練計劃"),
                create_level_bubble("🔥 高級者", "高級者訓練計劃"),
                create_level_bubble("🔙 返回", "返回")
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

# 初學者訓練計劃
def show_beginner_training_plan(event):
    flex_message = FlexSendMessage(
        alt_text="初學者訓練計劃",
        contents={
            "type": "bubble",
            "hero": {
                "type": "image",
                "url": "https://i.imgur.com/beginner_training.jpg",  # 替換為有效的圖片URL
                "size": "full",
                "aspectRatio": "20:13",
                "aspectMode": "cover",
                "action": {"type": "uri", "uri": "https://yourwebsite.com/beginner-plan"}
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",  # 減少間距
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
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",
                "contents": [
                    {"type": "button", "style": "link", "action": {"type": "message", "label": "🔙 返回選擇", "text": "返回"}}
                ]
            }
        }
    )
    line_bot_api.reply_message(event.reply_token, flex_message)

# 中級者訓練計劃
def show_intermediate_training_plan(event):
    flex_message = FlexSendMessage(
        alt_text="中級者訓練計劃",
        contents={
            "type": "bubble",
            "hero": {
                "type": "image",
                "url": "https://i.imgur.com/intermediate_training.jpg",  # 替換為有效的圖片URL
                "size": "full",
                "aspectRatio": "20:13",
                "aspectMode": "cover",
                "action": {"type": "uri", "uri": "https://yourwebsite.com/intermediate-plan"}
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",  # 減少間距
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
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",
                "contents": [
                    {"type": "button", "style": "link", "action": {"type": "message", "label": "🔙 返回選擇", "text": "返回"}}
                ]
            }
        }
    )
    line_bot_api.reply_message(event.reply_token, flex_message)

# 高級者訓練計劃
def show_advanced_training_plan(event):
    flex_message = FlexSendMessage(
        alt_text="高級者訓練計劃",
        contents={
            "type": "bubble",
            "hero": {
                "type": "image",
                "url": "https://i.imgur.com/advanced_training.jpg",  # 替換為有效的圖片URL
                "size": "full",
                "aspectRatio": "20:13",
                "aspectMode": "cover",
                "action": {"type": "uri", "uri": "https://yourwebsite.com/advanced-plan"}
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",  # 減少間距
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
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",
                "contents": [
                    {"type": "button", "style": "link", "action": {"type": "message", "label": "🔙 返回選擇", "text": "返回"}}
                ]
            }
        }
    )
    line_bot_api.reply_message(event.reply_token, flex_message)

# 顯示運動教學選單
def show_exercise_tutorial(event):
    flex_message = FlexSendMessage(
        alt_text="運動教學選單",
        contents={
            "type": "carousel",
            "contents": [
                create_tutorial_bubble("深蹲", "深蹲"),
                create_tutorial_bubble("伏地挺身", "伏地挺身"),
                create_tutorial_bubble("仰臥起坐", "仰臥起坐"),
                create_tutorial_bubble("引體向上", "引體向上"),
                create_tutorial_bubble("🔙 返回", "返回")
            ]
        }
    )
    line_bot_api.reply_message(event.reply_token, flex_message)

def create_tutorial_bubble(title, text):
    return {
        "type": "bubble",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "text", "text": title, "weight": "bold", "size": "lg"},
                {"type": "text", "text": f"選擇「{title}」來查看教學影片。", "size": "sm", "color": "#555555"}
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
                    "action": {"type": "message", "label": "觀看影片", "text": text}
                }
            ]
        }
    }

# 運動教學影片
def send_exercise_video(event, exercise):
    video_urls = {
        "深蹲": "https://www.youtube.com/watch?v=aclHkVaku9U",
        "伏地挺身": "https://www.youtube.com/watch?v=IODxDxX7oi4",
        "仰臥起坐": "https://www.youtube.com/watch?v=MKmrqcoCZ-M",
        "引體向上": "https://www.youtube.com/watch?v=9N4oPlpgf9w"
    }

    if exercise in video_urls:
        video_url = video_urls[exercise]
        flex_message = FlexSendMessage(
            alt_text=f"{exercise}教學影片",
            contents={
                "type": "bubble",
                "hero": {
                    "type": "image",
                    "url": "https://i.imgur.com/exercise_video.jpg",  # 替換為有效的影片縮圖URL
                    "size": "full",
                    "aspectRatio": "16:9",
                    "aspectMode": "cover",
                    "action": {"type": "uri", "uri": video_url}
                },
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {"type": "text", "text": f"{exercise} 教學影片", "weight": "bold", "size": "xl"},
                        {"type": "text", "text": "點擊圖片觀看教學影片。", "size": "sm", "color": "#555555"}
                    ]
                },
                "footer": {
                    "type": "box",
                    "layout": "vertical",
                    "spacing": "sm",
                    "contents": [
                        {"type": "button", "style": "link", "action": {"type": "message", "label": "🔙 返回選擇", "text": "返回"}}
                    ]
                }
            }
        )
        line_bot_api.reply_message(event.reply_token, flex_message)
    else:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="❌ 未找到該運動的教學影片！"))

# 查詢最近的健身房
@handler.add(MessageEvent, message=LocationMessage)
def handle_location_message(event):
    location = {
        'lat': event.message.latitude,
        'lng': event.message.longitude
    }
    show_nearest_gym(event, location)

def show_nearest_gym(event, location):
    # 使用 Google Maps 搜尋 URL 查詢最近健身房
    google_maps_url = f"https://www.google.com/maps/search/?api=1&query=gym&location={location['lat']},{location['lng']}"

    # 回傳健身房搜尋連結
    flex_message = FlexSendMessage(
        alt_text="最近的健身房",
        contents={
            "type": "bubble",
            "hero": {
                "type": "image",
                "url": "https://i.imgur.com/nearest_gym.jpg",  # 替換為有效的圖片URL
                "size": "full",
                "aspectRatio": "20:13",
                "aspectMode": "cover",
                "action": {"type": "uri", "uri": google_maps_url}
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",
                "contents": [
                    {"type": "text", "text": "📍 附近的健身房", "weight": "bold", "size": "xl"},
                    {"type": "text", "text": "點擊圖片查看最近的健身房位置。", "size": "sm", "color": "#555555"}
                ]
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",
                "contents": [
                    {"type": "button", "style": "link", "action": {"type": "uri", "label": "🔗 查看地圖", "uri": google_maps_url}},
                    {"type": "button", "style": "link", "action": {"type": "message", "label": "🔙 返回選擇", "text": "返回"}}
                ]
            }
        }
    )
    line_bot_api.reply_message(event.reply_token, flex_message)

# 顯示體態紀錄選單（輸入紀錄或查詢紀錄）
def show_body_record_menu(event):
    flex_message = FlexSendMessage(
        alt_text="體態紀錄選單",
        contents={
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",
                "contents": [
                    {"type": "text", "text": "📊 體態紀錄", "weight": "bold", "size": "xl"},
                    {"type": "text", "text": "請選擇您要進行的操作：", "size": "sm", "color": "#555555"}
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
                        "action": {"type": "message", "label": "✍️ 輸入紀錄", "text": "輸入紀錄"}
                    },
                    {
                        "type": "button",
                        "style": "primary",
                        "action": {"type": "message", "label": "📚 查詢紀錄", "text": "查詢紀錄"}
                    },
                    {
                        "type": "button",
                        "style": "primary",
                        "action": {"type": "message", "label": "🔙 返回", "text": "返回"}
                    }
                ]
            }
        }
    )
    line_bot_api.reply_message(event.reply_token, flex_message)

# 提示使用者輸入體態紀錄
def prompt_body_record_input(event):
    flex_message = FlexSendMessage(
        alt_text="體態紀錄輸入",
        contents={
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",  # 減少間距
                "contents": [
                    {"type": "text", "text": "✍️ 輸入體態紀錄", "weight": "bold", "size": "xl"},
                    {"type": "text", "text": "請輸入您的體重和身高，或傳送「取消」來退出。", "size": "sm", "color": "#555555"},
                    {"type": "text", "text": "格式：體重（公斤） 身高（公分）", "size": "sm", "color": "#555555"}
                ]
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",
                "contents": [
                    {"type": "button", "style": "link", "action": {"type": "message", "label": "🔙 返回選擇", "text": "返回"}}
                ]
            }
        }
    )
    line_bot_api.reply_message(event.reply_token, flex_message)

# 顯示體態紀錄（查詢紀錄）
def show_body_records(event, page=1):
    user_id = event.source.user_id
    offset = (page - 1) * PAGE_SIZE
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM body_data WHERE user_id = ? ORDER BY time DESC LIMIT ? OFFSET ?", (user_id, PAGE_SIZE, offset))
        records = c.fetchall()
        c.execute("SELECT COUNT(*) FROM body_data WHERE user_id = ?", (user_id,))
        total_records = c.fetchone()[0]
    
    if not records:
        reply_message = "📋 您尚無任何體態紀錄。"
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_message))
        return
    
    reply_message = "📋 您的體態紀錄：\n\n"
    for idx, record in enumerate(records, start=offset + 1):
        reply_message += (
            f"• 第 {idx} 條紀錄：\n"
            f"  ⏰ 時間: {record['time']} \n"
            f"  ⚖️ 體重: {record['weight']} kg \n"
            f"  📏 身高: {record['height']} cm \n"
            f"  📊 BMI: {record['bmi']:.2f}\n\n"
        )
    
    # 計算總頁數
    total_pages = (total_records + PAGE_SIZE - 1) // PAGE_SIZE
    
    # 按鈕模板
    actions = []
    if page > 1:
        actions.append({"type": "message", "label": "⬅️ 上一頁", "text": "體態紀錄上一頁"})
    if page < total_pages:
        actions.append({"type": "message", "label": "下一頁 ➡️", "text": "體態紀錄下一頁"})
    
    # 更新使用者狀態
    user_states[user_id] = {'state': 'viewing_body_records', 'page': page}
    
    # 如果有多頁，附加導航按鈕
    if actions:
        buttons_template = TemplateSendMessage(
            alt_text="體態紀錄導航",
            template=ButtonsTemplate(
                text=f"第 {page} 頁，共 {total_pages} 頁",
                actions=actions
            )
        )
        line_bot_api.reply_message(event.reply_token, [TextSendMessage(text=reply_message), buttons_template])
    else:
        # 單頁無需導航按鈕
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_message))

# 處理訓練計劃
def handle_training_plan(event):
    show_training_plan_menu(event)

# 處理飲食指導
def handle_diet_guidance(event):
    user_id = event.source.user_id
    user_states[user_id] = {'state': 'awaiting_diet_input'}
    
    flex_message = FlexSendMessage(
        alt_text="飲食指導輸入",
        contents={
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",
                "contents": [
                    {"type": "text", "text": "🍎 飲食指導", "weight": "bold", "size": "xl"},
                    {"type": "text", "text": "請輸入您的體重和身高以計算BMI，並獲取每日菜單建議。\n\n格式：體重（公斤） 身高（公分）\n例如：70 175", "size": "sm", "color": "#555555"}
                ]
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",
                "contents": [
                    {"type": "button", "style": "link", "action": {"type": "message", "label": "🔙 返回選擇", "text": "返回"}}
                ]
            }
        }
    )
    line_bot_api.reply_message(event.reply_token, flex_message)


# 處理運動指導
def handle_exercise_guidance(event):
    show_exercise_guidance(event)

# 處理體態紀錄的輸入並回應當筆紀錄
def handle_body_record_input(event, weight, height):
    user_id = event.source.user_id
    height_m = height / 100
    bmi = calculate_bmi(weight, height)
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 儲存到資料庫
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute('''INSERT INTO body_data (user_id, weight, height, bmi, time)
                     VALUES (?, ?, ?, ?, ?)''', 
                     (user_id, weight, height, bmi, current_time))
        conn.commit()

    # 生成每日菜單建議
    daily_menu = recommend_daily_menu(bmi)

    # 回應當筆紀錄和每日菜單
    reply_message = (
        f"✅ 體態紀錄成功！\n"
        f"📅 記錄時間：{current_time}\n"
        f"⚖️ 體重：{weight} kg\n"
        f"📏 身高：{height} cm\n"
        f"📊 BMI：{bmi:.2f}\n\n"
        f"{daily_menu}"
    )

    # 清除狀態
    del user_states[user_id]

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_message))

# 處理體態紀錄的查詢分頁
def handle_body_record_pagination(event, direction):
    user_id = event.source.user_id
    if user_id not in user_states:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="❌ 無法找到您的紀錄狀態。"))
        return
    
    state = user_states[user_id]
    if state.get('state') != 'viewing_body_records':
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="❌ 您目前沒有瀏覽紀錄。"))
        return
    
    current_page = state.get('page', 1)
    if direction == "上一頁" and current_page > 1:
        new_page = current_page - 1
    elif direction == "下一頁":
        new_page = current_page + 1
    else:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="❌ 無法進行分頁操作。"))
        return
    
    show_body_records(event, page=new_page)

# 處理體態紀錄相關的訊息
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    user_message = event.message.text.strip()

    # 檢查使用者是否在等待輸入
    if user_id in user_states:
        state = user_states[user_id]
        if state.get('state') == 'awaiting_body_record_input':
            if user_message.lower() in ["取消", "返回"]:
                del user_states[user_id]
                reply_message = "❌ 已取消體態紀錄。"
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_message))
                show_main_menu(event)
                return
            try:
                weight, height = map(float, user_message.split())
                handle_body_record_input(event, weight, height)
            except ValueError:
                error_message = "❌ 請按照正確格式輸入體重和身高，例如：80 180，或傳送「取消」退出。"
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text=error_message))
            except Exception as e:
                print(f"Error while recording body data: {e}")
                error_message = "❌ 發生錯誤，請稍後再試。"
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text=error_message))
            return
        elif state.get('state') == 'awaiting_diet_input':
            if user_message.lower() in ["取消", "返回"]:
                del user_states[user_id]
                reply_message = "❌ 已取消飲食指導。"
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_message))
                show_main_menu(event)
                return
            try:
                weight, height = map(float, user_message.split())
                bmi = calculate_bmi(weight, height)
                daily_menu = recommend_daily_menu(bmi)
                # 回應BMI和每日菜單
                reply_message = (
                    f"✅ BMI 計算結果：{bmi:.2f}\n\n"
                    f"📋 根據您的BMI，我們為您推薦以下每日菜單：\n\n{daily_menu}"
                )
                # 清除狀態
                del user_states[user_id]
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_message))
            except ValueError:
                error_message = "❌ 請按照正確格式輸入體重和身高，例如：70 175，或傳送「取消」退出。"
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text=error_message))
            except Exception as e:
                print(f"Error while processing diet input: {e}")
                error_message = "❌ 發生錯誤，請稍後再試。"
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text=error_message))
            return

    # 處理主功能選擇
    if user_message == "開始":
        show_main_menu(event)
        return

    elif user_message == "運動目標":
        show_exercise_goal(event)
        return

    elif user_message == "減脂":
        show_fat_loss_plan(event)
        return

    elif user_message == "增肌":
        show_muscle_gain_plan(event)
        return

    elif user_message == "提高心肺功能":
        show_cardiovascular_plan(event)
        return

    elif user_message == "運動教學":
        show_exercise_tutorial(event)
        return

    elif user_message == "運動指導":
        handle_exercise_guidance(event)
        return

    elif user_message == "體態紀錄":
        # 顯示體態紀錄選單
        show_body_record_menu(event)
        return

    elif user_message == "輸入紀錄":
        # 設置狀態，等待用戶輸入
        user_states[user_id] = {'state': 'awaiting_body_record_input'}
        prompt_body_record_input(event)
        return

    elif user_message == "查詢紀錄":
        # 顯示體態紀錄（第一頁）
        show_body_records(event, page=1)
        return

    elif user_message == "返回":
        show_main_menu(event)
        return

    elif user_message in ["深蹲", "伏地挺身", "仰臥起坐", "引體向上"]:
        send_exercise_video(event, user_message)
        return

    elif user_message in ["飲食指導", "🍎 飲食指導"]:
        handle_diet_guidance(event)
        return

    elif user_message in ["訓練計劃", "📋 訓練計劃"]:
        handle_training_plan(event)
        return

    elif user_message in ["初階者飲食方案", "👶 初階者飲食方案"]:
        show_beginner_diet_plan(event)
        return
    elif user_message in ["中級者飲食方案", "💪 中級者飲食方案"]:
        show_intermediate_diet_plan(event)
        return
    elif user_message in ["高級者飲食方案", "🔥 高級者飲食方案"]:
        show_advanced_diet_plan(event)
        return

    elif user_message in ["初學者訓練計劃", "👶 初學者訓練計劃"]:
        show_beginner_training_plan(event)
        return
    elif user_message in ["中級者訓練計劃", "💪 中級者訓練計劃"]:
        show_intermediate_training_plan(event)
        return
    elif user_message in ["高級者訓練計劃", "🔥 高級者訓練計劃"]:
        show_advanced_training_plan(event)
        return

    else:
        # 如果使用者發送位置以外的無效選項
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="❌ 請選擇有效選項！"))
        return


if __name__ == "__main__":
    # 建議在生產環境中使用更安全的方式來運行 Flask，例如使用 gunicorn
    app.run(host='0.0.0.0', port=5000)