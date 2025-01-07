import matplotlib.pyplot as plt
import uuid
import os
from linebot.models import ImageSendMessage
from .body_record import get_db_connection
def generate_weight_chart(user_id, database, num_records=10):
    print("開始生成體重圖表...")
    with get_db_connection(database) as conn:
        c = conn.cursor()
        c.execute("SELECT time, weight FROM body_data WHERE user_id = ? ORDER BY time ASC LIMIT ?", (user_id, num_records))
        data = c.fetchall()
    
    if not data:
        raise ValueError("No data available for chart generation.")
    
    times = [record['time'] for record in data]
    weights = [record['weight'] for record in data]
    
    print(f"取得的時間紀錄：{times}")
    print(f"取得的體重紀錄：{weights}")
    
    plt.figure(figsize=(10, 5))
    plt.plot(times, weights, marker='o', linestyle='-', color='b')
    plt.title('最近體重變化')
    plt.xlabel('時間')
    plt.ylabel('體重 (kg)')
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    # 生成唯一的檔名
    filename = f"{user_id}_{uuid.uuid4().hex}.png"
    img_path = os.path.join('img', filename)
    plt.savefig(img_path)
    plt.close()
    
    print(f"圖表已保存至 {img_path}")
    
    # 生成圖片的URL
    server_url = os.getenv("SERVER_URL")
    if not server_url:
        raise ValueError("SERVER_URL is not set in environment variables.")
    
    image_url = f"{server_url}/img/{filename}"
    print(f"圖表的URL：{image_url}")
    return image_url
