from scripts.db.db import close_db, connect_db, get_db_connection
from mysql.connector import Error

class Item:
    def __init__(self, item_data):
        self.item_id = item_data['item_id']
        self.item_name = item_data['item_name']
        self.item_description = item_data['description']

    def get_buy_price(self):
        return ItemDatabase.get_item_price(self.item_id, 'buy')
    
    def get_sell_price(self):
        return ItemDatabase.get_item_price(self.item_id, 'sell')
    
class ItemDatabase:
    def __init__(self, db_config):
        self.db_config = db_config

    @staticmethod
    def get_all_items():
        """Get all items with error handling"""
        connection = None
        try:
            connection = get_db_connection()
            cursor = connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT DISTINCT
                    i.item_id,
                    i.item_name,
                    i.description
                FROM item_transactions it
                JOIN items i ON it.item_id = i.item_id
                WHERE it.transaction_type IN ('sell', 'buy')
            """)
            items = [Item(item_data) for item_data in cursor.fetchall()]
            return items
            
        except Error as e:
            print(f"Error getting items: {e}")
            # Return fallback items
            return [
                Item({'item_id': 1, 'item_name': 'Corn Seeds', 'description': 'Plant corn'}),
                Item({'item_id': 2, 'item_name': 'Tomato Seeds', 'description': 'Plant tomatoes'}),
                Item({'item_id': 3, 'item_name': 'Wood', 'description': 'Building material'})
            ]
        finally:
            if connection:
                close_db(connection)
    
    def get_item_from_name(item_name):
        connection = connect_db()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM items WHERE item_name = %s"
        , (item_name,))
        item = cursor.fetchone()
        cursor.close()
        close_db(connection)

        return Item(item)

    def get_item_price(item_id, transaction_type):
        """Lấy giá của item theo transaction_type ('buy' hoặc 'sell')"""
        connection = connect_db()
        cursor = connection.cursor()

        # Truy vấn lấy giá của item theo item_id và transaction_type
        cursor.execute("""
            SELECT price
            FROM item_transactions
            WHERE item_id = %s AND transaction_type = %s
            LIMIT 1
        """, (item_id, transaction_type))

        # Lấy kết quả truy vấn
        result = cursor.fetchone()

        if result:
            return result[0]  # Trả về giá của item
        else:
            return None  # Nếu không có giao dịch tương ứng, trả về None

    def get_transaction_type(item_id):
        """Lấy giá của item theo transaction_type ('buy' hoặc 'sell')"""
        connection = connect_db()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT transaction_type
            FROM item_transactions
            WHERE item_id = %s
            LIMIT 1
        """, (item_id))

        result = cursor.fetchone()

        if result:
            return result[0]  
        else:
            return None