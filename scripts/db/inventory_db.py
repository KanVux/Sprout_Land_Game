from scripts.db.db import DatabaseConnection, Error, close_db
from scripts.db.item_db import Item

class InventoryItem(Item):
    def __init__(self, item_data):
        if isinstance(item_data, Item):
            item_data = {
                'item_id': item_data.item_id,
                'item_name': item_data.item_name,
                'description': item_data.item_description
            }
        
        super().__init__(item_data)
        self.quantity = item_data.get('quantity', 1)
    
    def increase_quantity(self, amount=1):
        self.quantity += amount
    
    def decrease_quantity(self, amount=1):
        if self.quantity >= amount:
            self.quantity -= amount
            return True
        return False

class Inventory:
    def __init__(self, inventory_data=None):
        self.items = []
        if inventory_data:
            for item in inventory_data:
                if item:
                    self.items.append(InventoryItem(item))
    
    def add_item(self, item_data, quantity=1):
        """Add item to inventory or increase quantity if exists"""
        # First, try to find existing item of the same type anywhere in inventory
        for item in self.items:
            if item is not None and item.item_name == item_data.item_name:
                item.increase_quantity(quantity)
                return True
        
        # If no existing item found, then look for empty slot
        empty_slot = -1
        for i, item in enumerate(self.items):
            if item is None:
                empty_slot = i
                break
        
        # Create new item
        new_item = InventoryItem(item_data)
        new_item.quantity = quantity
        
        # Add to empty slot or append
        if empty_slot >= 0:
            self.items[empty_slot] = new_item
        else:
            self.items.append(new_item)
        return True

    def remove_item(self, item_name, quantity=1):
        """Remove item quantity, remove item if quantity reaches 0"""
        for i, item in enumerate(self.items):
            if item and item.item_name == item_name:  # Check if item exists
                if item.decrease_quantity(quantity):
                    if item.quantity <= 0 and not item.item_name == 'coins':
                        self.items[i] = None  # Replace with None instead of removing
                    return True
        return False
    
    def get_item(self, item_name):
        """Lấy thông tin vật phẩm trong inventory"""
        item_name_lower = item_name.lower()
        
        for item in self.items:
            if isinstance(item, InventoryItem):
                # So sánh tên chính xác
                if item.item_name.lower() == item_name_lower:
                    return item
                    
                # Trường hợp đặc biệt cho seeds
                if " seeds" in item_name_lower and item.item_name.lower().replace(" seeds", "") == item_name_lower.replace(" seeds", ""):
                    return item
        
        return None
    

class InventoryDatabase:
    @staticmethod
    def get_player_inventory(player_id):
        connection = None
        cursor = None
        try:
            connection = DatabaseConnection.get_instance().connect()
            if not connection:
                return Inventory()
                
            cursor = connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT 
                    i.item_id,
                    i.item_name,
                    i.description,
                    inv.quantity,
                    inv.slot_number
                FROM inventory inv
                JOIN items i ON inv.item_id = i.item_id
                WHERE inv.player_id = %s order by inv.slot_number
            """, (str(player_id),))
            
            inventory_data = cursor.fetchall()
            return Inventory(inventory_data)
            
        except Error as e:
            print(f"Error getting inventory: {e}")
            return Inventory()
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    @staticmethod
    def save_inventory(player_id, inventory):
        db = DatabaseConnection.get_instance()
        
        # Prepare all operations
        operations = []
        
        # Add delete operation
        operations.append((
            "DELETE FROM inventory WHERE player_id = %s",
            (str(player_id),)
        ))
        
        # Add insert operations
        for index, item in enumerate(inventory.items):
            if item is not None:
                operations.append((
                    """INSERT INTO inventory (player_id, item_id, quantity, slot_number)
                       VALUES (%s, %s, %s, %s)""",
                    (str(player_id), item.item_id, item.quantity, index)
                ))
        # Execute all operations in single transaction
        return db.execute_transaction(operations)
