
import psycopg2
from psycopg2.extras import RealDictCursor
from app.core.config import settings
from typing import List, Dict

class PostgresHandler:
    def __init__(self):
        self.conn = None
        self.cursor = None

    def connect(self):
        try:
            self.conn = psycopg2.connect(
                dbname=settings.POSTGRES_DB,
                user=settings.POSTGRES_USER,
                password=settings.POSTGRES_PASSWORD,
                host=settings.POSTGRES_HOST,
                port=settings.POSTGRES_PORT
            )
            self.cursor = self.conn.cursor(cursor_factory=RealDictCursor)
            print("PostgreSQL database connection established.")
        except Exception as e:
            print(f"Error connecting to PostgreSQL: {e}")
            raise

    def disconnect(self):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        print("PostgreSQL database connection closed.")

    def execute_query(self, query: str, params=None) -> List[Dict]:
        """Execute a query and return results"""
        if not self.conn or self.conn.closed:
            self.connect()
        try:
            self.cursor.execute(query, params)
            result = self.cursor.fetchall()
            # Convert RealDictRow to regular dict
            return [dict(row) for row in result] if result else []
        except Exception as e:
            print(f"Error executing query: {e}")
            if self.conn:
                self.conn.rollback()
            raise

    def execute_command(self, query: str, params=None):
        """Execute a command (INSERT, UPDATE, DELETE) without return"""
        if not self.conn or self.conn.closed:
            self.connect()
        try:
            self.cursor.execute(query, params)
            self.conn.commit()
        except Exception as e:
            print(f"Error executing command: {e}")
            if self.conn:
                self.conn.rollback()
            raise

    def get_all_products(self) -> List[Dict]:
        """Get all active products"""
        query = "SELECT * FROM products WHERE is_active = true ORDER BY name;"
        return self.execute_query(query)

    def get_product_by_id(self, product_id: str) -> Dict:
        """Get a specific product by ID"""
        query = "SELECT * FROM products WHERE id = %s AND is_active = true;"
        result = self.execute_query(query, (product_id,))
        return result[0] if result else None

    def get_products_by_tags(self, tags: List[str]) -> List[Dict]:
        """Get products that match any of the provided tags"""
        if not tags:
            return []
        
        # Use product_tag instead of tags for the new schema
        query = """
        SELECT *, 
               CASE 
                   WHEN product_tag && %s THEN 
                       (SELECT COUNT(*) FROM unnest(product_tag) tag WHERE tag = ANY(%s)) 
                   ELSE 0 
               END as tag_matches
        FROM products 
        WHERE product_tag && %s AND is_active = true
        ORDER BY tag_matches DESC, rating DESC
        LIMIT 10;
        """
        return self.execute_query(query, (tags, tags, tags))

    def search_products_by_name(self, search_term: str) -> List[Dict]:
        """Search products by name or description"""
        query = """
        SELECT * FROM products 
        WHERE (LOWER(name) LIKE LOWER(%s) OR LOWER(description) LIKE LOWER(%s))
        AND is_active = true
        ORDER BY name;
        """
        search_pattern = f"%{search_term}%"
        return self.execute_query(query, (search_pattern, search_pattern))

    def get_products_by_category(self, category_id: str) -> List[Dict]:
        """Get products by category"""
        query = "SELECT * FROM products WHERE category_id = %s AND is_active = true ORDER BY name;"
        return self.execute_query(query, (category_id,))

    def update_product_stock(self, product_id: str, new_stock: int):
        """Update product stock count"""
        query = "UPDATE products SET stock_count = %s, updated_at = NOW() WHERE id = %s;"
        self.execute_command(query, (new_stock, product_id))

postgres_handler = PostgresHandler()
