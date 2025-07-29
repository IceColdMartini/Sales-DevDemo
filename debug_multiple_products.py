#!/usr/bin/env python3
"""
🔍 MULTIPLE PRODUCT REQUEST DEBUG
Testing why multiple product requests only return single products
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"
HEADERS = {"Content-Type": "application/json"}

def clear_conversation(sender_id):
    payload = {"sender": sender_id, "recipient": "page", "text": "/clear"}
    try:
        requests.post(f"{BASE_URL}/api/webhook", headers=HEADERS, data=json.dumps(payload))
        time.sleep(0.5)
    except:
        pass

def send_message(sender_id, message):
    payload = {"sender": sender_id, "recipient": "page", "text": message}
    try:
        response = requests.post(f"{BASE_URL}/api/webhook", headers=HEADERS, data=json.dumps(payload))
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except:
        return None

def test_multiple_product_issues():
    print("🔍 MULTIPLE PRODUCT REQUEST DEBUG")
    print("=" * 60)
    
    test_cases = [
        "I need perfume, face wash, and shampoo",
        "Looking for shampoo and face wash",
        "I want face wash and perfume",
        "Show me perfume, soap, and hair oil"
    ]
    
    for i, message in enumerate(test_cases, 1):
        print(f"\n🧪 TEST {i}: Multiple Product Request")
        print("-" * 40)
        print(f"👤 Customer: {message}")
        
        sender_id = f"multi_test_{i}"
        clear_conversation(sender_id)
        
        response = send_message(sender_id, message)
        if response:
            print(f"🤖 Agent: {response.get('response_text', '')[:150]}...")
            print(f"🛍️  Products: {response.get('product_interested', 'None')}")
            product_ids = response.get('interested_product_ids', [])
            print(f"🆔 Product IDs: {len(product_ids)} IDs")
            
            # Count detected categories
            products_text = response.get('product_interested', '').lower()
            categories = []
            if 'perfume' in products_text: categories.append('perfume')
            if 'face wash' in products_text or 'wash' in products_text: categories.append('face wash')
            if 'shampoo' in products_text: categories.append('shampoo')
            if 'soap' in products_text: categories.append('soap')
            if 'oil' in products_text: categories.append('oil')
            
            print(f"📊 Categories detected: {len(categories)} ({', '.join(categories)})")
            
            # Expected vs actual
            expected_categories = []
            if 'perfume' in message.lower(): expected_categories.append('perfume')
            if 'face wash' in message.lower(): expected_categories.append('face wash')
            if 'shampoo' in message.lower(): expected_categories.append('shampoo')
            if 'soap' in message.lower(): expected_categories.append('soap')
            if 'oil' in message.lower(): expected_categories.append('oil')
            
            print(f"📋 Expected categories: {len(expected_categories)} ({', '.join(expected_categories)})")
            
            if len(categories) >= len(expected_categories):
                print("✅ GOOD: All categories detected")
            else:
                print("❌ ISSUE: Missing categories")
        
        time.sleep(1)

def test_sequential_requests():
    """Test if asking for products one by one works better"""
    print("\n🔄 SEQUENTIAL REQUEST TEST")
    print("=" * 60)
    print("Testing if asking for products individually works better")
    
    sender_id = "sequential_test"
    clear_conversation(sender_id)
    
    products_to_track = []
    
    # Step 1: Ask for perfume
    print("\n👤 Step 1: I need a good perfume")
    response1 = send_message(sender_id, "I need a good perfume")
    if response1:
        print(f"🛍️  Products: {response1.get('product_interested', 'None')}")
        ids1 = response1.get('interested_product_ids', [])
        print(f"🆔 IDs: {len(ids1)}")
        products_to_track.extend(ids1)
    
    time.sleep(1)
    
    # Step 2: Add face wash
    print("\n👤 Step 2: I also need a face wash")
    response2 = send_message(sender_id, "I also need a face wash")
    if response2:
        print(f"🛍️  Products: {response2.get('product_interested', 'None')}")
        ids2 = response2.get('interested_product_ids', [])
        print(f"🆔 IDs: {len(ids2)}")
        
        # Check if previous products are retained
        if all(id in ids2 for id in products_to_track):
            print("✅ GOOD: Previous products retained")
        else:
            print("❌ ISSUE: Previous products lost")
            print(f"   Expected: {products_to_track}")
            print(f"   Current: {ids2}")
        
        products_to_track = ids2
    
    time.sleep(1)
    
    # Step 3: Add shampoo
    print("\n👤 Step 3: And I need shampoo too")
    response3 = send_message(sender_id, "And I need shampoo too")
    if response3:
        print(f"🛍️  Products: {response3.get('product_interested', 'None')}")
        ids3 = response3.get('interested_product_ids', [])
        print(f"🆔 IDs: {len(ids3)}")
        
        # Check final product count
        expected_categories = 3  # perfume, face wash, shampoo
        if len(ids3) >= expected_categories:
            print(f"✅ SUCCESS: {len(ids3)} products tracked (expected: {expected_categories}+)")
        else:
            print(f"❌ ISSUE: Only {len(ids3)} products tracked, expected {expected_categories}+")

if __name__ == "__main__":
    print("🚨 DEBUGGING MULTIPLE PRODUCT REQUEST ISSUES")
    print("Understanding why multiple product requests don't work properly")
    print()
    
    test_multiple_product_issues()
    test_sequential_requests()
    
    print("\n" + "=" * 60)
    print("🔧 DEBUG COMPLETE")
    print("Review the results to understand multiple product handling issues")
