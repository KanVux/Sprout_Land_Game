from scripts.db.db import get_db_connection
from mysql.connector import Error

class MissionDatabase:
    @staticmethod
    def get_connection():
        """
        Lấy connection thông qua db.py (sử dụng singleton).
        """
        connection = get_db_connection()
        if connection:
            return connection
        else:
            return None

    @staticmethod
    def get_all_missions():
        """Lấy danh sách tất cả nhiệm vụ chung."""
        connection = MissionDatabase.get_connection()
        if connection is None:
            return []
        cursor = connection.cursor(dictionary=True)
        try:
            sql = """SELECT 
                mission_id, name, description, type, npc_assigned, 
                reward_item, reward_quantity, required_progress,
                prerequisite_missions, story_stage, previous_mission_id, next_mission_id
            FROM missions"""
            cursor.execute(sql)
            result = cursor.fetchall()
            return result
        except Error as e:
            print(f"Error in get_all_missions: {e}")
            return []
        finally:
            cursor.close()

    @staticmethod
    def get_player_missions(player_id):
        """Load nhiệm vụ của một người chơi."""
        connection = MissionDatabase.get_connection()
        if connection is None:
            return []
        cursor = connection.cursor(dictionary=True)
        try:
            sql = """SELECT pm.*, m.name, m.description, m.type, m.npc_assigned, m.reward_item, 
                     m.reward_quantity, m.required_progress
                     FROM player_missions AS pm 
                     JOIN missions AS m ON pm.mission_id = m.mission_id 
                     WHERE player_id = %s"""
            player_id_str = str(player_id)  # Chuyển đổi player_id thành chuỗi
            cursor.execute(sql, (player_id_str,))
            result = cursor.fetchall()
            return result
        except Error as e:
            print(f"Error in get_player_missions: {e}")
            return []
        finally:
            cursor.close()

    @staticmethod
    def save_player_mission(player_id, mission_data):
        """
        Lưu nhiệm vụ của người chơi:
        mission_data: dictionary gồm các keys:
            - mission_id
            - status (active hoặc completed)
            - progress (tiến độ hiện tại)
            - date_assigned (ngày giao nhiệm vụ)
        Nếu mission đã tồn tại thì update, ngược lại thì insert.
        """
        connection = MissionDatabase.get_connection()
        if connection is None:
            return
        cursor = connection.cursor()
        try:
            sql = """
                INSERT INTO player_missions (player_id, mission_id, status, progress, date_assigned)
                VALUES (%s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE status = %s, progress = %s, date_assigned = %s
                """
            params = (
                str(player_id),
                mission_data['mission_id'],
                mission_data['status'],
                mission_data['progress'],
                mission_data['date_assigned'],
                mission_data['status'],
                mission_data['progress'],
                mission_data['date_assigned']
            )
            cursor.execute(sql, params)
            connection.commit()
        except Error as e:
            connection.rollback()
            print(f"Error in save_player_mission: {e}")
        finally:
            cursor.close()