# filepath: /c:/Users/a0973/OneDrive/桌面/程式設計2上/1109/1219.py
import os
import google.generativeai as generativeai
from dotenv import load_dotenv

# 加載 .env 文件中的環境變數
load_dotenv()

# 配置 Google Generative AI API 金鑰
api_key = os.getenv("key")
generativeai.configure(api_key=api_key)

# 生成內容
response = generativeai.GenerativeModel('gemini-2.0-flash-exp').generate_content('妳是誰？')
print(response.text)