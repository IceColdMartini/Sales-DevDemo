#!/usr/bin/env python3
"""
🔍 FACE WASH DETECTION DEBUG
Testing why face wash isn't being detected in multiple product scenarios
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

def test_face_wash_detection():
    print("🔍 FACE WASH DETECTION DEBUG")
    print("=" * 60)
    
    # Test 1: Single face wash request
    print("\n✅ TEST 1: Single Face Wash Request")
    print("-" * 40)
    
    sender_id = "face_wash_single"
    clear_conversation(sender_id)
    
    print("👤 Customer: I need a face wash")
    response = send_message(sender_id, "I need a face wash")
    if response:
        print(f"🤖 Agent: {response.get('response_text', '')[:100]}...")
        print(f"🛍️  Products: {response.get('product_interested', 'None')}")
        product_ids = response.get('interested_product_ids', [])
        print(f"🆔 Product IDs: {len(product_ids)} IDs: {product_ids}")
        
        # Check if face wash is detected
        products_text = response.get('product_interested', '').lower()
        if 'face wash' in products_text or 'wash' in products_text:
            print("✅ SUCCESS: Face wash properly detected")
        else:
            print("❌ ISSUE: Face wash not detected")
    
    # Test 2: Multiple products including face wash (the failing scenario)
    print("\n❌ TEST 2: Multiple Products Including Face Wash (FAILING)")
    print("-" * 40)
    
    sender_id = "face_wash_multiple"
    clear_conversation(sender_id)
    
    # Step 1: Ask for multiple products including face wash
    print("👤 Customer: I need perfume, face wash, and shampoo")
    response1 = send_message(sender_id, "I need perfume, face wash, and shampoo")
    if response1:
        print(f"🤖 Agent: {response1.get('response_text', '')[:150]}...")
        print(f"🛍️  Step 1 Products: {response1.get('product_interested', 'None')}")
        product_ids = response1.get('interested_product_ids', [])
        print(f"🆔 Step 1 IDs: {len(product_ids)} IDs")
        
        # Check what products were detected
        products_text = response1.get('product_interested', '').lower()
        has_perfume = 'perfume' in products_text
        has_face_wash = 'face wash' in products_text or 'wash' in products_text
        has_shampoo = 'shampoo' in products_text
        
        print(f"   Perfume detected: {has_perfume}")
        print(f"   Face wash detected: {has_face_wash}")
        print(f"   Shampoo detected: {has_shampoo}")
        
        if not has_face_wash:
            print("❌ ISSUE: Face wash missing in multiple product request")
    
    time.sleep(1)
    
    # Step 2: Follow up question about face wash specifically
    print("\n👤 Customer: What about the face wash options?")
    response2 = send_message(sender_id, "What about the face wash options?")
    if response2:
        print(f"🤖 Agent: {response2.get('response_text', '')[:150]}...")
        print(f"🛍️  Step 2 Products: {response2.get('product_interested', 'None')}")
        product_ids = response2.get('interested_product_ids', [])
        print(f"🆔 Step 2 IDs: {len(product_ids)} IDs")
        
        # Check if face wash is now detected
        products_text = response2.get('product_interested', '').lower()
        if 'face wash' in products_text or 'wash' in products_text:
            print("✅ GOOD: Face wash detected on specific inquiry")
        else:
            print("❌ STILL MISSING: Face wash not detected even on specific inquiry")

def test_keyword_extraction():
    """Test what keywords are being extracted for face wash"""
    print("\n🔍 KEYWORD EXTRACTION TEST")
    print("-" * 40)
    
    # This would require direct access to the AI service, but we can infer from responses
    test_messages = [
        "I need a face wash",
        "I need perfume, face wash, and shampoo",
        "What about face wash options?",
        "Show me some face cleansers"
    ]
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n🧪 Test {i}: '{message}'")
        sender_id = f"keyword_test_{i}"
        clear_conversation(sender_id)
        
        response = send_message(sender_id, message)
        if response:
            products = response.get('product_interested', 'None')
            has_face_product = any(word in products.lower() for word in ['face', 'wash', 'cleanser'])
            print(f"   Face product detected: {has_face_product}")
            print(f"   Products: {products}")

if __name__ == "__main__":
    print("🚨 DEBUGGING FACE WASH DETECTION ISSUES")
    print("Understanding why face wash isn't detected in multiple product scenarios")
    print()
    
    test_face_wash_detection()
    test_keyword_extraction()
    
    print("\n" + "=" * 60)
    print("🔧 DEBUG COMPLETE")
    print("Review the results to understand face wash detection issues")
