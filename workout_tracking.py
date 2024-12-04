from datetime import datetime, timedelta
import mongodb

class WorkoutTracker:
    def __init__(self):
        self.db = mongodb.DatabaseManager()

    def record_workout(self, user_id, workout_details):
        """記錄用戶運動"""
        try:
            # workout_details 應包含：type, duration, calories
            result = self.db.record_workout(
                user_id, 
                workout_details['type'],
                workout_details['duration'],
                workout_details['calories']
            )
            
            return f"成功記錄{workout_details['type']}運動，持續{workout_details['duration']}分鐘"
        except Exception as e:
            return f"記錄運動失敗：{str(e)}"

    def generate_workout_report(self, user_id):
        """生成用戶運動報告"""
        workouts = self.db.get_user_workouts(user_id)
        
        if not workouts:
            return "尚無運動記錄"
        
        # 分析運動數據
        total_duration = sum(workout['duration'] for workout in workouts)
        total_calories = sum(workout['calories'] for workout in workouts)
        workout_types = set(workout['type'] for workout in workouts)
        
        report = f"""
📊 本週運動報告 🏋️
- 總運動時間：{total_duration}分鐘
- 總消耗卡路里：{total_calories}卡
- 運動類型：{', '.join(workout_types)}
- 運動次數：{len(workouts)}次
        """
        
        return report

    def get_workout_suggestions(self, user_id):
        """根據用戶運動歷史提供建議"""
        workouts = self.db.get_user_workouts(user_id, days=30)
        
        if not workouts:
            return "建議嘗試多種運動以找到適合自己的"
        
        # 統計最常做的運動
        workout_counts = {}
        for workout in workouts:
            workout_counts[workout['type']] = workout_counts.get(workout['type'], 0) + 1
        
        most_common_workout = max(workout_counts, key=workout_counts.get)
        
        suggestions = {
            '跑步': ['間歇跑', '長距離慢跑', '斜坡跑'],
            '重訓': ['高強度間歇訓練', '肌肉群交叉訓練', '漸進式重量訓練'],
            '游泳': ['自由泳技巧訓練', '不同泳姿訓練', '水中有氧'],
            # 可根據實際情況擴展
        }
        
        return f"根據你的運動習慣，推薦嘗試：{suggestions.get(most_common_workout, ['多樣化訓練'])}"

# 使用範例
if __name__ == '__main__':
    tracker = WorkoutTracker()
    
    # 記錄運動
    workout_details = {
        'type': '跑步',
        'duration': 45,
        'calories': 350
    }
    print(tracker.record_workout('user123', workout_details))
    
    # 生成報告
    print(tracker.generate_workout_report('user123'))
    
    # 獲取建議
    print(tracker.get_workout_suggestions('user123'))