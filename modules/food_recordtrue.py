# modules/food_record.py

import sqlite3
import logging
from datetime import datetime
import os
import json
from PIL import Image
import io
from google import generativeai
import traceback
import re

# 配置日誌
logger = logging.getLogger(__name__)

# 設定日誌等級和格式
logging.basicConfig(
    level=logging.INFO,  # 在開發和調試時，可將等級設置為 DEBUG
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

# 設定 Generative AI (Gemini) API 金鑰
google_api_key = os.getenv("GOOGLE_GENERATIVEAI_API_KEY")

    

# 資料庫檔案位置
FOOD_RECORD_DB = 'food_record.db'

def get_db_connection():
    """建立與 SQLite 資料庫的連接。"""
    try:
        conn = sqlite3.connect(FOOD_RECORD_DB)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        logger.error(f"建立資料庫連接時出錯: {e}")
        raise

def initialize_database():
    """初始化飲食紀錄資料庫，確保必要的表格存在。"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS diet_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                food_item TEXT NOT NULL,
                calories REAL NOT NULL,
                timestamp TEXT NOT NULL
            );
        ''')
        conn.commit()
        conn.close()
        logger.info("初始化 food_record.db 並確保 diet_records 表格存在。")
    except Exception as e:
        logger.error(f"初始化資料庫時出錯: {e}")
        raise

def recognize_food_items(image_data):
    """
    使用 Gemini 辨識圖片中的食物項目並估算其熱量。
    
    參數:
    - image_data (bytes): 圖片數據
    
    返回:
    - list of dict: 辨識出的食物名稱及其熱量
    """
    try:
        # 初始化 Gemini 模型進行圖片辨識和熱量估算
        model = generativeai.GenerativeModel('gemini-2.0-flash-exp')  # 使用適當的模型

        # 將圖片數據轉換為 PIL Image
        image_file = Image.open(io.BytesIO(image_data))

        # 設計提示，要求 Gemini 以 JSON 格式返回食物名稱和熱量
        prompt = (
            "Identify all the food items present in this image and provide the estimated calories for each item. "
            "Respond only with a JSON array in the following format without any additional text:\n\n"
            "[\n"
            "    {\n"
            '        "food_item": "Apple",\n'
            '        "calories": 95\n'
            "    },\n"
            "    {\n"
            '        "food_item": "Sandwich",\n'
            '        "calories": 250\n'
            "    }\n"
            "]"
        )

        # 發送圖片和提示至 Gemini
        response = model.generate_content([image_file, prompt])

        # 記錄 Gemini 的原始回應
        logger.info(f"Gemini 原始回應: {response.text}")

        # 檢查回應是否為空
        if not response.text.strip():
            logger.error("Gemini 返回空白回應。")
            return []

        # 使用正則表達式移除反引號和任何語言標籤
        cleaned_response = re.sub(r'^```(?:json)?\s*', '', response.text.strip())
        cleaned_response = re.sub(r'\s*```$', '', cleaned_response)

        # 嘗試解析 JSON
        food_items = json.loads(cleaned_response)

        # 驗證 food_items 是否為列表
        if not isinstance(food_items, list):
            logger.error(f"Gemini 返回的 JSON 不是列表。實際類型：{type(food_items)}")
            logger.error(f"Gemini 回應內容: {cleaned_response}")
            return []

        # 確認每個項目都是字典並包含 'food_item' 和 'calories'
        validated_food_items = []
        for item in food_items:
            if isinstance(item, dict) and 'food_item' in item and 'calories' in item:
                # 確保熱量為數值類型
                try:
                    calories = float(item['calories'])
                except (ValueError, TypeError):
                    calories = 0  # 或其他適當的預設值
                validated_food_items.append({
                    'food_item': item['food_item'],
                    'calories': calories
                })
            else:
                logger.warning(f"無效的食物項目格式：{item}")

        logger.info(f"辨識出的食物項目及熱量：{validated_food_items}")
        return validated_food_items

    except json.JSONDecodeError as e:
        logger.error(f"解析 Gemini 的 JSON 回應時出錯：{e}")
        logger.error(f"Gemini 回應內容: {response.text}")
        return []
    except Exception as e:
        logger.error(f"使用 Gemini 辨識食物項目及熱量時出錯：{e}, traceback: {traceback.format_exc()}")
        return []

def save_food_record(user_id, food_items):
    """
    儲存辨識出的食物項目及其熱量資訊到飲食紀錄。
    
    參數:
    - user_id (str): LINE 使用者 ID
    - food_items (list of dict): 辨識出的食物名稱及其熱量列表
    """
    try:
        if not isinstance(food_items, list):
            logger.error(f"food_items 的類型不是列表。實際類型：{type(food_items)}")
            return

        conn = get_db_connection()
        cursor = conn.cursor()
        timestamp = datetime.now().isoformat()

        for item in food_items:
            if not isinstance(item, dict):
                logger.warning(f"food_items 中的項目不是字典：{item}")
                continue
            if 'food_item' not in item or 'calories' not in item:
                logger.warning(f"food_items 中的項目缺少必要的鍵：{item}")
                continue

            food = item['food_item']
            calories = item['calories']

            cursor.execute('''
                INSERT INTO diet_records (user_id, food_item, calories, timestamp)
                VALUES (?, ?, ?, ?)
            ''', (user_id, food, calories, timestamp))
        
        conn.commit()
        conn.close()
        logger.info(f"已儲存用戶 {user_id} 的食物紀錄：{food_items}")
    except Exception as e:
        logger.error(f"儲存用戶 {user_id} 的食物紀錄時出錯: {e}")
        raise

def get_diet_records(user_id, limit=10, offset=0):
    """
    獲取使用者的飲食紀錄，包括食物名稱和熱量。
    
    參數:
    - user_id (str): LINE 使用者 ID
    - limit (int): 每頁顯示的紀錄數量
    - offset (int): 紀錄偏移量
    
    返回:
    - list of dict: 飲食紀錄列表
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT food_item, calories, timestamp FROM diet_records
            WHERE user_id = ?
            ORDER BY timestamp DESC
            LIMIT ? OFFSET ?
        ''', (user_id, limit, offset))
        rows = cursor.fetchall()
        conn.close()

        records = [{'food_item': row['food_item'], 'calories': row['calories'], 'timestamp': row['timestamp']} for row in rows]
        logger.info(f"已獲取用戶 {user_id} 的 {len(records)} 條飲食紀錄。")
        return records
    except Exception as e:
        logger.error(f"獲取用戶 {user_id} 的飲食紀錄時出錯: {e}")
        raise
