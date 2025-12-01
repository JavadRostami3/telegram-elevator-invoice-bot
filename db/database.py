"""
Database Manager Module
Handles all database operations for the Elevator Invoice Bot
"""
import sqlite3
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import os


class DatabaseManager:
    """Manages SQLite database operations"""
    
    def __init__(self, db_path: str = "elevator_bot.db"):
        """Initialize database connection"""
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self) -> sqlite3.Connection:
        """Get a database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        return conn
    
    def init_database(self):
        """Initialize database with all required tables"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Create products table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT,
                name TEXT NOT NULL,
                unit TEXT NOT NULL,
                price INTEGER NOT NULL,
                system TEXT NOT NULL,
                type TEXT NOT NULL,
                factor REAL DEFAULT 0,
                base_add REAL DEFAULT 0,
                name_pattern TEXT,
                stops_offset INTEGER DEFAULT 0,
                category TEXT,
                is_active INTEGER DEFAULT 1,
                min_floors INTEGER,
                max_floors INTEGER
            )
        ''')
        
        # Create invoices table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS invoices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_name TEXT NOT NULL,
                project_name TEXT NOT NULL,
                system TEXT NOT NULL,
                floors INTEGER NOT NULL,
                total_price INTEGER NOT NULL,
                created_at TEXT NOT NULL
            )
        ''')
        
        # Create invoice_items table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS invoice_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_id INTEGER NOT NULL,
                product_id INTEGER,
                name TEXT NOT NULL,
                unit TEXT NOT NULL,
                quantity REAL NOT NULL,
                unit_price INTEGER NOT NULL,
                total_price INTEGER NOT NULL,
                FOREIGN KEY (invoice_id) REFERENCES invoices(id),
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        ''')
        
        # Create settings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    # ==================== PRODUCTS CRUD ====================
    
    def add_product(self, code: str, name: str, unit: str, price: int,
                   system: str, type: str, factor: float = 0, base_add: float = 0,
                   name_pattern: str = None, stops_offset: int = 0,
                   category: str = None, is_active: int = 1,
                   min_floors: int = None, max_floors: int = None) -> int:
        """Add a new product to database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO products (code, name, unit, price, system, type,
                                factor, base_add, name_pattern, stops_offset,
                                category, is_active, min_floors, max_floors)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (code, name, unit, price, system, type, factor, base_add,
              name_pattern, stops_offset, category, is_active, min_floors, max_floors))
        
        product_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return product_id
    
    def get_products(self, system_type: str = None, is_active: int = 1,
                    floors: int = None) -> List[Dict]:
        """
        Get products from database with filters
        
        Args:
            system_type: 'hydraulic' or 'gearless' (None for all)
            is_active: 1 for active, 0 for inactive
            floors: Number of floors for min/max filtering
        
        Returns:
            List of product dictionaries
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        query = "SELECT * FROM products WHERE is_active = ?"
        params = [is_active]
        
        if system_type:
            query += " AND (system = ? OR system = 'common')"
            params.append(system_type)
        
        if floors is not None:
            query += " AND (min_floors IS NULL OR min_floors <= ?)"
            query += " AND (max_floors IS NULL OR max_floors >= ?)"
            params.extend([floors, floors])
        
        cursor.execute(query, params)
        products = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return products
    
    def get_product_by_id(self, product_id: int) -> Optional[Dict]:
        """Get a single product by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
        row = cursor.fetchone()
        conn.close()
        
        return dict(row) if row else None
    
    def update_product_price(self, product_id: int, new_price: int) -> bool:
        """Update product price"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "UPDATE products SET price = ? WHERE id = ?",
            (new_price, product_id)
        )
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return success
    
    def update_product(self, product_id: int, **kwargs) -> bool:
        """Update product fields dynamically"""
        if not kwargs:
            return False
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Build UPDATE query dynamically
        set_clause = ", ".join([f"{key} = ?" for key in kwargs.keys()])
        values = list(kwargs.values()) + [product_id]
        
        query = f"UPDATE products SET {set_clause} WHERE id = ?"
        cursor.execute(query, values)
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return success
    
    def delete_product(self, product_id: int) -> bool:
        """Delete a product (or just deactivate it)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Soft delete by setting is_active = 0
        cursor.execute(
            "UPDATE products SET is_active = 0 WHERE id = ?",
            (product_id,)
        )
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return success
    
    # ==================== INVOICES CRUD ====================
    
    def create_invoice(self, customer_name: str, project_name: str,
                      system: str, floors: int, total_price: int) -> int:
        """Create a new invoice"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        created_at = datetime.now().isoformat()
        
        cursor.execute('''
            INSERT INTO invoices (customer_name, project_name, system,
                                floors, total_price, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (customer_name, project_name, system, floors, total_price, created_at))
        
        invoice_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return invoice_id
    
    def get_invoice(self, invoice_id: int) -> Optional[Dict]:
        """Get invoice by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM invoices WHERE id = ?", (invoice_id,))
        row = cursor.fetchone()
        conn.close()
        
        return dict(row) if row else None
    
    def get_all_invoices(self, limit: int = 50) -> List[Dict]:
        """Get all invoices (limited)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM invoices ORDER BY created_at DESC LIMIT ?",
            (limit,)
        )
        invoices = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return invoices
    
    # ==================== INVOICE ITEMS CRUD ====================
    
    def add_invoice_item(self, invoice_id: int, product_id: int,
                        name: str, unit: str, quantity: float,
                        unit_price: int, total_price: int) -> int:
        """Add an item to an invoice"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO invoice_items (invoice_id, product_id, name, unit,
                                      quantity, unit_price, total_price)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (invoice_id, product_id, name, unit, quantity, unit_price, total_price))
        
        item_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return item_id
    
    def get_invoice_items(self, invoice_id: int) -> List[Dict]:
        """Get all items for an invoice"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM invoice_items WHERE invoice_id = ?",
            (invoice_id,)
        )
        items = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return items
    
    # ==================== SETTINGS CRUD ====================
    
    def set_setting(self, key: str, value: str):
        """Set a setting value"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            (key, value)
        )
        
        conn.commit()
        conn.close()
    
    def get_setting(self, key: str, default: str = None) -> Optional[str]:
        """Get a setting value"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = cursor.fetchone()
        conn.close()
        
        return row['value'] if row else default
    
    def get_all_settings(self) -> Dict[str, str]:
        """Get all settings as dictionary"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT key, value FROM settings")
        settings = {row['key']: row['value'] for row in cursor.fetchall()}
        conn.close()
        
        return settings
