#!/usr/bin/env python3
"""
Product Catalog Management Script
Add, update, and manage products in the Sales Agent database
"""

import psycopg2
import json
import uuid
from datetime import datetime
from typing import List, Dict, Optional

class ProductCatalogManager:
    def __init__(self, db_config: Dict[str, str]):
        self.conn = psycopg2.connect(**db_config)
        self.cursor = self.conn.cursor()

    def add_product(self, product_data: Dict) -> str:
        """Add a single product to the catalog"""
        product_id = str(uuid.uuid4())
        
        query = """
        INSERT INTO products (
            id, name, slug, description, price, sale_price, stock_count,
            image_url, images, rating, review_count, is_active, 
            category_id, product_tag
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
        """
        
        values = (
            product_id,
            product_data['name'],
            product_data.get('slug', product_data['name'].lower().replace(' ', '-')),
            product_data['description'],
            product_data['price'],
            product_data.get('sale_price'),
            product_data.get('stock_count', 0),
            product_data.get('image_url', ''),
            product_data.get('images', []),
            product_data.get('rating', 0.0),
            product_data.get('review_count', 0),
            product_data.get('is_active', True),
            product_data.get('category_id', str(uuid.uuid4())),
            product_data.get('product_tag', [])
        )
        
        self.cursor.execute(query, values)
        self.conn.commit()
        print(f"✅ Added product: {product_data['name']} (ID: {product_id})")
        return product_id

    def add_products_batch(self, products: List[Dict]) -> List[str]:
        """Add multiple products at once"""
        product_ids = []
        for product in products:
            try:
                product_id = self.add_product(product)
                product_ids.append(product_id)
            except Exception as e:
                print(f"❌ Failed to add {product.get('name', 'Unknown')}: {e}")
        return product_ids

    def list_products(self) -> List[Dict]:
        """List all products in the catalog"""
        query = "SELECT * FROM products WHERE is_active = true ORDER BY name"
        self.cursor.execute(query)
        
        columns = [desc[0] for desc in self.cursor.description]
        products = []
        
        for row in self.cursor.fetchall():
            product = dict(zip(columns, row))
            products.append(product)
        
        return products

    def delete_product(self, product_id: str) -> bool:
        """Soft delete a product (set is_active = false)"""
        query = "UPDATE products SET is_active = false WHERE id = %s"
        self.cursor.execute(query, (product_id,))
        affected = self.cursor.rowcount
        self.conn.commit()
        
        if affected > 0:
            print(f"✅ Deleted product with ID: {product_id}")
            return True
        else:
            print(f"❌ Product not found: {product_id}")
            return False

    def close(self):
        """Close database connection"""
        self.cursor.close()
        self.conn.close()

# Sample product templates
SAMPLE_PRODUCTS = [
    {
        "name": "Wild Stone Edge Perfume",
        "description": "Fresh and energetic fragrance with citrus and aquatic notes. Perfect for active lifestyle.",
        "price": 395.00,
        "sale_price": 349.00,
        "stock_count": 120,
        "image_url": "https://example.com/wildstone-edge.jpg",
        "images": ["https://example.com/wildstone-edge.jpg"],
        "rating": 4.2,
        "review_count": 134,
        "product_tag": ["perfume", "masculine", "fresh", "citrus", "active", "energetic", "fragrance"]
    },
    {
        "name": "Premium Casual Shirt",
        "description": "100% cotton casual shirt with modern fit. Available in multiple colors.",
        "price": 1299.00,
        "sale_price": 999.00,
        "stock_count": 45,
        "image_url": "https://example.com/casual-shirt.jpg", 
        "images": ["https://example.com/casual-shirt.jpg"],
        "rating": 4.1,
        "review_count": 67,
        "product_tag": ["shirt", "cotton", "casual", "clothing", "men", "fashion", "modern"]
    },
    {
        "name": "Smartwatch Pro",
        "description": "Advanced smartwatch with fitness tracking, heart rate monitor, and 7-day battery life.",
        "price": 8999.00,
        "sale_price": 6999.00,
        "stock_count": 25,
        "image_url": "https://example.com/smartwatch.jpg",
        "images": ["https://example.com/smartwatch.jpg"],
        "rating": 4.6,
        "review_count": 203,
        "product_tag": ["smartwatch", "fitness", "technology", "wearable", "health", "sports", "electronics"]
    }
]

def main():
    # Database configuration
    db_config = {
        'host': 'localhost',
        'port': 5432,
        'database': 'sales_db',
        'user': 'user',
        'password': 'password'
    }
    
    # Initialize manager
    manager = ProductCatalogManager(db_config)
    
    print("🛍️ Product Catalog Manager")
    print("=" * 50)
    
    while True:
        print("\nOptions:")
        print("1. Add single product")
        print("2. Add sample products")
        print("3. List all products") 
        print("4. Delete product")
        print("5. Exit")
        
        choice = input("\nEnter your choice (1-5): ").strip()
        
        if choice == "1":
            # Add single product
            print("\nEnter product details:")
            name = input("Name: ")
            description = input("Description: ")
            price = float(input("Price: "))
            sale_price_input = input("Sale Price (press Enter to skip): ")
            sale_price = float(sale_price_input) if sale_price_input else None
            stock = int(input("Stock Count: "))
            
            # Product tags
            print("Enter product tags (comma-separated):")
            tags_input = input("Tags: ")
            tags = [tag.strip() for tag in tags_input.split(",") if tag.strip()]
            
            product_data = {
                "name": name,
                "description": description,
                "price": price,
                "sale_price": sale_price,
                "stock_count": stock,
                "product_tag": tags
            }
            
            try:
                manager.add_product(product_data)
            except Exception as e:
                print(f"❌ Error adding product: {e}")
        
        elif choice == "2":
            # Add sample products
            print("\nAdding sample products...")
            manager.add_products_batch(SAMPLE_PRODUCTS)
        
        elif choice == "3":
            # List products
            products = manager.list_products()
            print(f"\n📦 Found {len(products)} products:")
            print("-" * 80)
            for product in products:
                print(f"• {product['name']} - ₹{product['price']}")
                print(f"  Tags: {', '.join(product.get('product_tag', []))}")
                print(f"  Stock: {product['stock_count']}")
                print()
        
        elif choice == "4":
            # Delete product
            product_id = input("\nEnter product ID to delete: ")
            manager.delete_product(product_id)
        
        elif choice == "5":
            print("\n👋 Goodbye!")
            break
        
        else:
            print("❌ Invalid choice. Please try again.")
    
    manager.close()

if __name__ == "__main__":
    main()
