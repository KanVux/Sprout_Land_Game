import mysql.connector
from mysql.connector import Error
from .db import DatabaseConnection
import json

class SettingsDB:	
	@staticmethod
	def get_settings():	
		"""
		Retrieve settings from the 'settings' table.
		Assumes a table structure:
			settingsid INT PRIMARY KEY,
			volume SMALLINT,
			keys_bind JSON
		"""
		db = DatabaseConnection.get_instance()
		connection = db.connect()
		cursor = None
		settings = {}
		try:
			cursor = connection.cursor(dictionary=True)
			# assuming there is a single settings record with settingsid = 1
			cursor.execute("SELECT volume, keys_bind FROM settings WHERE idsettings = 1")
			row = cursor.fetchone()
			if row:
				settings['volume'] = row['volume']
				# Convert JSON string to dict:
				settings['keys_bind'] = json.loads(row['keys_bind']) if row['keys_bind'] else {}
			cursor.close()
			connection.close()
		except Error as e:
			print("Error retrieving settings:", e)
		return settings
	
	@staticmethod
	def save_setting(volume, keys_bind):
		"""
		Save or update settings in the database.
		Uses an INSERT ... ON DUPLICATE KEY UPDATE query.
		The table structure is expected to have a single record with settingsid = 1.
		"""
		db = DatabaseConnection.get_instance()
		connection = db.connect()
		cursor = None
		try:
			cursor = connection.cursor()
			# Convert keys_bind dictionary to JSON string
			keys_bind_json = json.dumps(keys_bind)
			query = """
				INSERT INTO settings (idsettings, volume, keys_bind)
				VALUES (1, %s, %s)
				ON DUPLICATE KEY UPDATE volume = %s, keys_bind = %s
			"""
			cursor.execute(query, (volume, keys_bind_json, volume, keys_bind_json))
			connection.commit()
			cursor.close()
			connection.close()
			print("Settings saved successfully.")
		except Error as e:
			print("Error saving settings:", e)

if __name__ == '__main__':
	settings = SettingsDB.get_settings()
	print(settings)
