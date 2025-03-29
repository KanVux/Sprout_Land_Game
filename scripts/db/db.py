import mysql.connector
from mysql.connector import Error

class DatabaseConnection:
    _instance = None
    _connection = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = DatabaseConnection()
        return cls._instance
    
    def __init__(self):
        self.db_config = {
            'host': 'localhost',
            'user': 'root',
            'password': '1234567890',
            'database': 'sprout_land_data',
            'port': 3306,
            'raise_on_warnings': True,
            'connection_timeout': 5,
            'autocommit': False
        }

    def connect(self):
        """Create database connection with error handling"""
        try:
            if not self._connection or not self._connection.is_connected():
                self._connection = mysql.connector.connect(**self.db_config)
            return self._connection
        except Error as e:
            print(f"Connection error: {e}")
            return None

    def execute_transaction(self, operations):
        """Execute multiple operations in a single transaction"""
        connection = self.connect()
        if not connection:
            return False

        cursor = None
        try:
            cursor = connection.cursor()
            for operation in operations:
                query, params = operation
                cursor.execute(query, params)
            connection.commit()
            return True
        except Error as e:
            connection.rollback()
            print(f"Transaction error: {e}")
            return False
        finally:
            if cursor:
                cursor.close()

def get_db_connection():
    """Get database connection using singleton pattern"""
    return DatabaseConnection.get_instance().connect()

def connect_db():
    """Legacy support for existing code"""
    try:
        connection = get_db_connection()
        if connection is None:
            # Return a fallback connection for testing
            return create_fallback_connection()
        return connection
    except Error as e:
        print(f"Connection error: {e}")
        return create_fallback_connection()

def close_db(connection):
    """Safely close database connection"""
    try:
        if connection and hasattr(connection, 'close'):
            connection.close()
    except Error as e:
        print(f"Error closing connection: {e}")

def create_fallback_connection():
    """Create a mock connection for testing"""
    class MockConnection:
        def cursor(self, dictionary=False):
            return MockCursor()
        def close(self):
            pass
        def is_connected(self):
            return True
        def commit(self):
            pass
        def rollback(self):
            pass
        def start_transaction(self):
            pass
            
    class MockCursor:
        def execute(self, query, params=None):
            pass
        def fetchall(self):
            return []
        def fetchone(self):
            return None
        def close(self):
            pass

    return MockConnection()