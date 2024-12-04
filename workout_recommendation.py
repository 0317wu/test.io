import webbrowser

class 運動指導:
    def __init__(self):
        self.運動計劃 = {
            "初學者": ["伏地挺身：10次", "深蹲：15次", "平板支撐：30秒"],
            "中級者": ["伏地挺身：20次", "深蹲：25次", "平板支撐：60秒"],
            "高級者": ["伏地挺身：30次", "深蹲：40次", "平板支撐：90秒"]
        }
        self.運動影片 = {
            "伏地挺身": "https://www.youtube.com/watch?v=IODxDxX7oi4",
            "深蹲": "https://www.youtube.com/watch?v=aclHkVaku9U",
            "平板支撐": "https://www.youtube.com/watch?v=pSHjTRCQxIw"
        }
        self.運動記錄 = []

    def 查看運動計劃(self, 等級):
        print(f"\n適合 {等級} 的運動計劃：")
        for 運動 in self.運動計劃.get(等級, []):
            print(f" - {運動}")

    def 記錄運動(self, 運動名稱, 次數, 時間):
        self.運動記錄.append({
            "運動名稱": 運動名稱,
            "次數": 次數,
            "時間": 時間
        })
        print("運動記錄成功！")

    def 查看記錄(self):
        if not self.運動記錄:
            print("目前還沒有運動記錄！")
        else:
            print("\n運動記錄：")
            for 記錄 in self.運動記錄:
                print(f"- {記錄['運動名稱']} | 次數：{記錄['次數']} | 時間：{記錄['時間']}秒")

    def 播放運動影片(self, 運動名稱):
        if 運動名稱 in self.運動影片:
            print(f"正在打開 {運動名稱} 的教學影片...")
            webbrowser.open(self.運動影片[運動名稱])  # 打開瀏覽器播放影片
        else:
            print(f"抱歉，目前沒有 {運動名稱} 的教學影片。")

def 主程式():
    指導 = 運動指導()

    print("歡迎來到運動指導系統！")
    while True:
        print("\n請選擇功能：")
        print("1. 查看運動計劃")
        print("2. 記錄運動")
        print("3. 查看運動記錄")
        print("4. 播放運動教學影片")
        print("5. 離開系統")

        選擇 = input("輸入你的選擇：")
        if 選擇 == "1":
            print("請選擇你的運動等級：")
            print("1. 初學者")
            print("2. 中級者")
            print("3. 高級者")
            等級選擇 = input("輸入你的選擇：")
            等級對應 = {"1": "初學者", "2": "中級者", "3": "高級者"}
            等級 = 等級對應.get(等級選擇, "初學者")
            指導.查看運動計劃(等級)
        elif 選擇 == "2":
            運動名稱 = input("輸入運動名稱：")
            次數 = int(input("輸入運動次數（或重複數）："))
            時間 = int(input("輸入運動時間（秒）："))
            指導.記錄運動(運動名稱, 次數, 時間)
        elif 選擇 == "3":
            指導.查看記錄()
        elif 選擇 == "4":
            運動名稱 = input("輸入運動名稱以查看教學影片：")
            指導.播放運動影片(運動名稱)
        elif 選擇 == "5":
            print("感謝使用！保持健康，天天運動！")
            break
        else:
            print("輸入無效，請重新選擇！")

if __name__ == "__main__":
    主程式()
