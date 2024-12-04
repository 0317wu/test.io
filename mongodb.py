from pymongo import MongoClient
from datetime import datetime

class DatabaseManager:
    def __init__(self, connection_string='mongodb://localhost:27017/', db_name='fitness_bot'):
        try:
            self.client = MongoClient(connection_string)
            self.db = self.client[db_name]
            
            # 創建集合
            self.users_collection = self.db['users']
            self.workouts_collection = self.db['workouts']
            self.goals_collection = self.db['goals']
        except Exception as e:
            print(f"數據庫連接錯誤: {e}")

    def add_user(self, user_id, line_id, name):
        """添加新用戶"""
        user_data = {
            'user_id': user_id,
            'line_id': line_id,
            'name': name,
            'created_at': datetime.now()
        }
        return self.users_collection.insert_one(user_data)

    def record_workout(self, user_id, workout_type, duration, calories):
        """記錄用戶運動"""
        workout_data = {
            'user_id': user_id,
            'type': workout_type,
            'duration': duration,
            'calories': calories,
            'date': datetime.now()
        }
        return self.workouts_collection.insert_one(workout_data)

    def get_user_workouts(self, user_id, days=7):
        """獲取用戶最近的運動記錄"""
        week_ago = datetime.now() - timedelta(days=days)
        return list(self.workouts_collection.find({
            'user_id': user_id,
            'date': {'$gte': week_ago}
        }))

    def set_fitness_goal(self, user_id, goal_type, target_value):
        """設定用戶健身目標"""
        goal_data = {
            'user_id': user_id,
            'type': goal_type,
            'target': target_value,
            'start_date': datetime.now(),
            'status': 'active'
        }
        return self.goals_collection.insert_one(goal_data)

    def get_active_goal(self, user_id):
        """獲取用戶當前活躍目標"""
        return self.goals_collection.find_one({
            'user_id': user_id,
            'status': 'active'
        })

# 使用範例
if __name__ == '__main__':
    db = DatabaseManager()
    
    # 添加用戶
    db.add_user('user123', 'line_user_123', '小明')
    
    # 記錄運動
    db.record_workout('user123', '跑步', 45, 350)
    
    # 設定目標
    db.set_fitness_goal('user123', '減重', '5公斤')