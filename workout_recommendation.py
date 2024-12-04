import random
import mongodb

class WorkoutRecommendation:
    def __init__(self):
        self.db = mongodb.DatabaseManager()
        
        # 運動庫
        self.workout_library = {
            '減重': [
                {'name': 'HIIT訓練', 'duration': 30, 'calories': 400, 'difficulty': '高'},
                {'name': '有氧操', 'duration': 45, 'calories': 300, 'difficulty': '中'},
                {'name': '跳繩', 'duration': 20, 'calories': 250, 'difficulty': '中'}
            ],
            '增肌': [
                {'name': '重量訓練-胸部', 'duration': 60, 'calories': 300, 'difficulty': '高'},
                {'name': '啞鈴訓練', 'duration': 45, 'calories': 250, 'difficulty': '中'},
                {'name': '核心力量訓練', 'duration': 30, 'calories': 200, 'difficulty': '中'}
            ],
            '塑形': [
                {'name': 'Tabata訓練', 'duration': 25, 'calories': 350, 'difficulty': '高'},
                {'name': '瑜伽', 'duration': 60, 'calories': 200, 'difficulty': '低'},
                {'name': '普拉提', 'duration': 45, 'calories': 250, 'difficulty': '中'}
            ]
        }

    def get_personalized_recommendation(self, user_id):
        """獲取個性化運動推薦"""
        # 獲取用戶的活躍目標
        active_goal = self.db.get_active_goal(user_id)
        
        if not active_goal:
            return "請先設定健身目標"
        
        goal_type = active_goal['type']
        
        # 從運動庫選擇
        workouts = self.workout_library.get(goal_type, [])
        
        if not workouts:
            return "暫無適合的運動建議"
        
        # 獲取用戶近期運動記錄
        recent_workouts = self.db.get_user_workouts(user_id, days=30)
        recent_workout_names = [w['type'] for w in recent_workouts]
        
        # 過濾已做過的運動
        available_workouts = [
            workout for workout in workouts 
            if workout['name'] not in recent_workout_names
        ]
        
        # 如果所有建議都做過，則重新推薦
        if not available_workouts:
            available_workouts = workouts
        
        # 隨機推薦
        recommended_workout = random.choice(available_workouts)
        
        recommendation = f"""
🏋️ 個性化運動推薦
- 運動：{recommended_workout['name']}
- 目標：{goal_type}
- 時長：{recommended_workout['duration']}分鐘
- 預計消耗：{recommended_workout['calories']}卡路里
- 難度：{recommended_workout['difficulty']}
        """
        
        return recommendation

    def get_video_recommendation(self, workout_name):
        """
        獲取運動影片建議
        實際實現需要連接YouTube API或其他視頻資源
        """
        video_links = {
            'HIIT訓練': 'https://youtube.com/example_hiit',
            '有氧操': 'https://youtube.com/example_aerobics',
            # 其他運動的YouTube連結
        }
        
        return video_links.get(workout_name, "暫無相關影片")

# 使用範例
if __name__ == '__main__':
    recommender = WorkoutRecommendation()
    
    # 獲取個性化推薦
    print(recommender.get_personalized_recommendation('user123'))
    
    # 獲取運動視頻
    print(recommender.get_video_recommendation('HIIT訓練'))