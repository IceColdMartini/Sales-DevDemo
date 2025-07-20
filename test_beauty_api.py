#!/usr/bin/env python3
"""
Test script for the enhanced beauty e-commerce LLM system
"""

import requests
import json

# Test the enhanced beauty product matching system
def test_beauty_queries():
    base_url = "http://localhost:8001"
    
    test_queries = [
        {
            "query": "I need something for my acne and oily skin",
            "expected_products": ["neem", "face wash", "acne control"]
        },
        {
            "query": "My hair is falling out, what can help?",
            "expected_products": ["hair fall", "shampoo", "oil"]
        },
        {
            "query": "I want a nice fragrance for special occasions",
            "expected_products": ["perfume", "fragrance", "premium"]
        },
        {
            "query": "Something to make my skin softer and moisturized",
            "expected_products": ["moisturizing", "soap", "cream"]
        },
        {
            "query": "Natural products for hair growth",
            "expected_products": ["coconut oil", "amla", "hair growth"]
        }
    ]
    
    print("🧪 Testing Enhanced Beauty E-commerce LLM System")
    print("=" * 60)
    
    for i, test in enumerate(test_queries, 1):
        print(f"\n🔍 Test {i}: {test['query']}")
        print("-" * 40)
        
        try:
            response = requests.post(
                f"{base_url}/api/webhook",
                json={
                    "sender": "test_user_123",
                    "recipient": "page_123", 
                    "text": test['query']
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Status: {response.status_code}")
                print(f"📝 Message: {result.get('response_text', 'No message')}")
                print(f"🚀 Ready: {result.get('is_ready', False)}")
                print(f"🛍️  Product Interest: {result.get('product_interested', 'None')}")
                
                # Check if products were found
                if 'products' in result:
                    products = result['products']
                    print(f"🛍️  Found {len(products)} products:")
                    for j, product in enumerate(products[:3], 1):  # Show top 3
                        print(f"   {j}. {product['name']} - ₹{product['price']}")
                        print(f"      📍 Tags: {', '.join(product['product_tag'][:5])}...")
                else:
                    print("❌ No products found in response")
                    
            else:
                print(f"❌ Status: {response.status_code}")
                print(f"📝 Error: {response.text}")
                
        except requests.exceptions.Timeout:
            print("⏰ Request timed out (30s)")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 Testing completed!")

def test_single_query():
    """Test a single specific query"""
    base_url = "http://localhost:8001"
    
    query = "I need something for dry damaged hair"
    print(f"🧪 Single Test: {query}")
    print("=" * 50)
    
    try:
        response = requests.post(
            f"{base_url}/api/webhook",
            json={
                "sender": "test_user_456",
                "recipient": "page_123",
                "text": query
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Response received successfully")
            print(f"📝 Message: {result.get('response_text')}")
            print(f"🚀 Ready: {result.get('is_ready')}")
            print(f"🛍️  Product Interest: {result.get('product_interested')}")
            
            if 'products' in result:
                products = result['products']
                print(f"\n🛍️  Found {len(products)} matching products:")
                for i, product in enumerate(products, 1):
                    print(f"\n{i}. {product['name']}")
                    print(f"   💰 Price: ₹{product['price']}")
                    print(f"   ⭐ Rating: {product['rating']}/5 ({product['review_count']} reviews)")
                    print(f"   📝 Description: {product['description'][:100]}...")
                    print(f"   🏷️  Top Tags: {', '.join(product['product_tag'][:8])}")
        else:
            print(f"❌ Error {response.status_code}: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    # Run single query test first
    test_single_query()
    
    print("\n\n")
    
    # Run comprehensive tests
    test_beauty_queries()
