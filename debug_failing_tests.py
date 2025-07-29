#!/usr/bin/env python3
"""
🔍 FOCUSED DEBUG: Face Wash Detection & Purchase Intent Issues
Testing the specific failing scenarios to identify root causes
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

def test_failing_scenarios():
    print("🔍 DEBUGGING FAILING TEST SCENARIOS")
    print("=" * 80)
    
    # Test 1: "I want to purchase this product" should be is_ready=True
    print("\n❌ FAILING TEST 1: 'I want to purchase this product'")
    print("-" * 60)
    
    sender_id = "debug_test_1"
    clear_conversation(sender_id)
    
    # First establish context
    print("👤 Setup: Hi, I'm interested in perfume")
    setup_response = send_message(sender_id, "Hi, I'm interested in perfume")
    if setup_response:
        print(f"🤖 Agent: {setup_response.get('response_text', '')[:100]}...")
        print(f"🛍️  Context Product: {setup_response.get('product_interested', 'None')}")
    
    time.sleep(1)
    
    # Now test the failing message
    print("\n👤 Test: I want to purchase this product")
    test_response = send_message(sender_id, "I want to purchase this product")
    if test_response:
        print(f"🤖 Agent: {test_response.get('response_text', '')[:150]}...")
        print(f"🛍️  Products: {test_response.get('product_interested', 'None')}")
        print(f"🆔 Product IDs: {test_response.get('interested_product_ids', [])}")
        print(f"🚀 Ready: {test_response.get('is_ready', False)}")
        
        if test_response.get('is_ready'):
            print("✅ FIXED: Now correctly returns is_ready=True")
        else:
            print("❌ STILL FAILING: Should be is_ready=True for 'this product'")
    
    # Test 2: Face wash detection
    print("\n\n❌ FAILING TEST 2: Face Wash Detection")
    print("-" * 60)
    
    sender_id = "debug_test_2"
    clear_conversation(sender_id)
    
    print("👤 Test: I need a face wash")
    response = send_message(sender_id, "I need a face wash")
    if response:
        print(f"🤖 Agent: {response.get('response_text', '')[:150]}...")
        print(f"🛍️  Products: {response.get('product_interested', 'None')}")
        print(f"🆔 Product IDs: {response.get('interested_product_ids', [])}")
        
        product_interested = response.get('product_interested', '')
        if 'face wash' in product_interested.lower() or 'wash' in product_interested.lower():
            print("✅ GOOD: Face wash detected correctly")
        else:
            print("❌ ISSUE: Face wash not properly detected")
            print(f"   Expected: Contains 'face wash'")
            print(f"   Actual: '{product_interested}'")
    
    # Test 3: Complete flow - final confirmation
    print("\n\n❌ FAILING TEST 3: Complete Flow Step 7")
    print("-" * 60)
    
    sender_id = "debug_test_3"
    clear_conversation(sender_id)
    
    # Build up conversation context
    messages = [
        "Hi, I need perfume",
        "Tell me about Wild Stone perfume",
        "What's the price?",
        "That sounds good",
        "I'm interested in buying it"
    ]
    
    print("🔄 Building conversation context...")
    for i, msg in enumerate(messages, 1):
        print(f"   Step {i}: {msg}")
        send_message(sender_id, msg)
        time.sleep(0.5)
    
    # Final confirmation that should trigger is_ready=True
    print("\n👤 Final Test: Yes, I'll take it")
    final_response = send_message(sender_id, "Yes, I'll take it")
    if final_response:
        print(f"🤖 Agent: {final_response.get('response_text', '')[:150]}...")
        print(f"🛍️  Products: {final_response.get('product_interested', 'None')}")
        print(f"🆔 Product IDs: {final_response.get('interested_product_ids', [])}")
        print(f"🚀 Ready: {final_response.get('is_ready', False)}")
        
        if final_response.get('is_ready'):
            print("✅ GOOD: Final confirmation triggers is_ready=True")
        else:
            print("❌ ISSUE: Final confirmation should trigger is_ready=True")
    
    # Test 4: Product retention across messages
    print("\n\n❌ FAILING TEST 4: Product Retention")
    print("-" * 60)
    
    sender_id = "debug_test_4"
    clear_conversation(sender_id)
    
    print("👤 Step 1: I need face wash and perfume")
    response1 = send_message(sender_id, "I need face wash and perfume")
    if response1:
        print(f"🛍️  Step 1 Products: {response1.get('product_interested', 'None')}")
        print(f"🆔 Step 1 IDs: {len(response1.get('interested_product_ids', []))} IDs")
    
    time.sleep(1)
    
    print("\n👤 Step 2: What are the prices?")
    response2 = send_message(sender_id, "What are the prices?")
    if response2:
        print(f"🛍️  Step 2 Products: {response2.get('product_interested', 'None')}")
        print(f"🆔 Step 2 IDs: {len(response2.get('interested_product_ids', []))} IDs")
        
        # Check if products were retained
        step1_ids = set(response1.get('interested_product_ids', []))
        step2_ids = set(response2.get('interested_product_ids', []))
        
        if step1_ids.issubset(step2_ids) and len(step2_ids) >= len(step1_ids):
            print("✅ GOOD: Products retained across conversation")
        else:
            print("❌ ISSUE: Products lost during conversation")
            print(f"   Step 1: {step1_ids}")
            print(f"   Step 2: {step2_ids}")

if __name__ == "__main__":
    print("🚨 DEBUGGING FAILING TEST SCENARIOS")
    print("Investigating specific issues from the failed tests")
    print()
    
    test_failing_scenarios()
    
    print("\n" + "=" * 80)
    print("🔧 DEBUGGING COMPLETE")
    print("Check the output above to identify specific issues to fix")
