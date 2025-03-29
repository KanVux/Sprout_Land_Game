import json
import uuid
from datetime import datetime

import pygame
from scripts.db.db import DatabaseConnection, Error

class PlayerData:
    def __init__(self, player_data):
        self.player_id = player_data['player_id']
        self.name = player_data['player_name']

class PlayerDatabase:
    @staticmethod
    def get_player_info(player_id):
        connection = None
        cursor = None
        try:
            connection = DatabaseConnection.get_instance().connect()
            if not connection:
                return None
                
            cursor = connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT * FROM players 
                WHERE player_id = %s
            """, (player_id,))
            
            player_data = cursor.fetchone()
            return PlayerData(player_data) if player_data else None
            
        except Error as e:
            print(f"Error getting player info: {e}")
            return None
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()
                
    @staticmethod
    def save_game_state(player_id, player_data, level_data):
        """Save complete game state"""
        db = DatabaseConnection.get_instance()
        connection = None
        cursor = None
        try:
            connection = db.connect()
            if not connection:
                return False
                
            cursor = connection.cursor()
            
            # Save player state with alias

            cursor.execute("""
                INSERT INTO game_states 
                    (player_id, position_x, position_y, game_time, is_raining)
                VALUES (%s, %s, %s, %s, %s) AS new_data
                ON DUPLICATE KEY UPDATE
                    position_x = new_data.position_x,
                    position_y = new_data.position_y,
                    game_time = new_data.game_time,
                    is_raining = new_data.is_raining
            """, (
                player_id,
                player_data['position'].x,
                player_data['position'].y,
                player_data['game_time'],
                level_data['is_raining']
            ))
            
            # Save world state with alias
            cursor.execute("""
                INSERT INTO world_states 
                    (player_id, soil_grid, planted_crops, trees_state, 
                    water_grid, time_of_day)
                VALUES (%s, %s, %s, %s, %s, %s) AS new_data
                ON DUPLICATE KEY UPDATE
                    soil_grid = new_data.soil_grid,
                    planted_crops = new_data.planted_crops,
                    trees_state = new_data.trees_state,
                    water_grid = new_data.water_grid,
                    time_of_day = new_data.time_of_day
            """, (
                player_id,
                json.dumps(level_data['soil_grid']),
                json.dumps(level_data['planted_crops']),
                json.dumps(level_data['trees_state']),
                json.dumps(level_data['water_grid']),
                level_data['time_of_day']
            ))
            
            connection.commit()
            return True
            
        except Error as e:
            if connection:
                connection.rollback()
            print(f"Error saving game state: {e}")
            return False
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()
                
    @staticmethod
    def load_game_state(player_id):
        """Load complete game state"""
        db = DatabaseConnection.get_instance()
        connection = None
        cursor = None
        try:
            connection = db.connect()
            if not connection:
                return None
                
            cursor = connection.cursor(dictionary=True)
            
            # Get player state
            cursor.execute("""
                SELECT * FROM game_states 
                WHERE player_id = %s
            """, (str(player_id),))
            game_state = cursor.fetchone()
            
            if not game_state:
                return None
                
            # Get world state
            cursor.execute("""
                SELECT * FROM world_states
                WHERE player_id = %s
            """, (str(player_id),))
            world_state = cursor.fetchone()
            
            if not world_state:
                return None
                
            # Return combined state
            return {
                'player': {
                    'position': pygame.math.Vector2(
                        game_state['position_x'],
                        game_state['position_y']
                    ),
                    'game_time': game_state['game_time'],
                },
                'level': {
                    'is_raining': bool(game_state['is_raining']),
                    'soil_grid': json.loads(world_state['soil_grid']),
                    'planted_crops': json.loads(world_state['planted_crops']),
                    'trees_state': json.loads(world_state['trees_state']),
                    'water_grid': json.loads(world_state['water_grid']),
                    'time_of_day': float(world_state['time_of_day'])
                }
            }
            
        except Error as e:
            print(f"Error loading game state: {e}")
            return None
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    @staticmethod
    def get_all_players():
        """Get all player characters from the database"""
        connection = None
        cursor = None
        try:
            connection = DatabaseConnection.get_instance().connect()
            if not connection:
                return []
                
            cursor = connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT player_id, player_name, created_at, last_played
                FROM players
                ORDER BY last_played DESC
            """)
            
            result = cursor.fetchall()
            return result
            
        except Error as e:
            print(f"Error getting all players: {e}")
            return []
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    @staticmethod
    def create_player(player_name):
        """Create a new player character"""
        connection = None
        cursor = None
        try:
            connection = DatabaseConnection.get_instance().connect()
            if not connection:
                return None
                
            player_id = str(uuid.uuid4())  # Generate unique ID 
            cursor = connection.cursor()
            
            # Create player entry
            cursor.execute("""
                INSERT INTO players (player_id, player_name, created_at, last_played)
                VALUES (%s, %s, NOW(), NOW())
            """, (player_id, player_name))
        
            
            connection.commit()
            return player_id
            
        except Error as e:
            if connection:
                connection.rollback()
            print(f"Error creating player: {e}")
            return None
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    @staticmethod
    def delete_player(player_id):
        """Delete a player character and all related data"""
        connection = None
        cursor = None
        try:
            connection = DatabaseConnection.get_instance().connect()
            if not connection:
                return False
                
            cursor = connection.cursor()
            
            # Delete related data first to maintain referential integrity
            for table in ["inventory", "player_missions", "game_states", "world_states"]:
                cursor.execute(f"DELETE FROM {table} WHERE player_id = %s", (player_id,))
            
            # Finally delete the player entry
            cursor.execute("DELETE FROM players WHERE player_id = %s", (player_id,))
            
            connection.commit()
            return True
            
        except Error as e:
            if connection:
                connection.rollback()
            print(f"Error deleting player: {e}")
            return False
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    @staticmethod
    def update_last_played(player_id):
        """Update the last_played timestamp for a player"""
        connection = None
        cursor = None
        try:
            connection = DatabaseConnection.get_instance().connect()
            if not connection:
                return False
                
            cursor = connection.cursor()
            cursor.execute("""
                UPDATE players 
                SET last_played = NOW()
                WHERE player_id = %s
            """, (player_id,))
            
            connection.commit()
            return True
            
        except Error as e:
            if connection:
                connection.rollback()
            print(f"Error updating last played: {e}")
            return False
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()
