import requests
import json
import os
from dotenv import load_dotenv
from linebot import LineBotApi

load_dotenv()

LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")

headers = {
    "Authorization":f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
    "Content-Type":"application/json"
}

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)

with open(r"D:\User\Desktop\BMICHART\test.io\richMenu.json", 'r', encoding='utf-8') as f:
    rich_menu_data = f.read()

req = requests.request('POST', 'https://api.line.me/v2/bot/richmenu', headers=headers, data=rich_menu_data)

print(req.text)

rich_menu_id = json.loads(req.text)['richMenuId']
if not rich_menu_id:
    raise ValueError("richMenuId not found in response")

with open(r'D:\User\Desktop\BMICHART\test.io\richMenu.png', "rb") as img:
    try:
        line_bot_api.set_rich_menu_image(rich_menu_id, "image/png", img)
        print("Image uploaded successfully!")
    except Exception as e:
        print("Error uploading image:", e)

start_rich_menu = requests.request('POST', f'https://api.line.me/v2/bot/user/all/richmenu/{rich_menu_id}', headers=headers)

print(start_rich_menu.text)