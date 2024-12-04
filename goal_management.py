from datetime import datetime, timedelta
import mongodb

class GoalManager:
    def __init__(self):
        self.db = mongodb.DatabaseManager()

    def set_fitness_goal(self, user_id, goal_type, target_value, target_date=None):
        """設定健身目標"""
        try:
            # 如果沒有指定目標日期，預設3個月
            if not target_date:
                target_date = datetime.now() + timedelta(days=90)
            
            goal_data = {
                'type': goal_type,
                'target_value': target_value,
                'target_date': target_date,
                'start_date': datetime.now(),
                'status': 'active'
            }
            
            self.db.set_fitness_goal(user_id, goal_type, goal_data)
            
            return f"成功設定{goal_type}目標：{target_value}"
        except Exception as e:
            return f"設定目標失敗：{str(e)}"

    def track_goal_progress(self, user_id):
        """追蹤目標進度"""
        active_goal = self.db.get_active_goal(user_id)
        
        if not active_goal:
            return "尚未設定目標"
        
        # 計算目標進度
        days_total = (active_goal['target_date'] - active_goal['start_date']).days
        days_passed = (datetime.now() - active_goal['start_date']).days
        progress_percentage = (days_passed / days_total) * 100
        
        # 根據目標類型獲取當前值（需要額外的邏輯和資料）
        current_value = self._get_current_goal_value(user_id, active_goal['type'])
        
        progress_report = f"""
🎯 目標追蹤報告
- 目標類型：{active_goal['type']}
- 目標值：{active_goal['target_value']}
- 當前進度：{current_value}
- 時間進度：{progress_percentage:.2f}%
- 剩餘時間：{days_total - days_passed}天
        """
        
        return progress_report

    def _get_current_goal_value(self, user_id, goal_type):
        """
        根據不同目標類型獲取當前值
        實際實現需要連接各種數據源
        """
        if goal_type == '減重':
            # 這裡應該從體重記錄中獲取
            return '尚未實現'
        elif goal_type == '增肌':
            # 從運動記錄和體重記錄計算
            return '尚未實現'
        return '未知'

# 使用範例
if __name__ == '__main__':
    goal_manager = GoalManager()
    
    # 設定目標
    print(goal_manager.set_fitness_goal('user123', '減重', '5公斤'))
    
    # 追蹤目標進度
    print(goal_manager.track_goal_progress('user123'))