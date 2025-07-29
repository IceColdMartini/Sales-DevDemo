#!/usr/bin/env python3
"""
🔍 FOCUSED TEST: Initial Purchase Intent vs Purchase Confirmation
Testing the specific scenario that's failing: "I want to buy Wild Stone perfume"
This should trigger is_ready=FALSE initially (purchase intent, not confirmation)
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"
HEADERS = {"Content-Type": "application/json"}

def test_api_health():
    """Check if API is running"""
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ Sales Agent API is healthy and ready")
            return True
        else:
            print(f"❌ API health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to API: {e}")
        return False

def clear_conversation(sender_id):
    """Clear conversation history for clean test"""
    payload = {"sender": sender_id, "recipient": "page", "text": "/clear"}
    try:
        requests.post(f"{BASE_URL}/api/webhook", headers=HEADERS, data=json.dumps(payload))
        time.sleep(0.5)
    except:
        pass

def send_message(sender_id, message):
    """Send message and return response"""
    payload = {"sender": sender_id, "recipient": "page", "text": message}
    
    try:
        response = requests.post(f"{BASE_URL}/api/webhook", headers=HEADERS, data=json.dumps(payload))
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ API Error: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return None

def test_initial_purchase_intent():
    """Test that 'I want to buy X' is treated as intent, not confirmation"""
    print("\n🔍 FOCUSED TEST: Initial Purchase Intent Detection")
    print("=" * 70)
    print("Testing: 'I want to buy Wild Stone perfume' should be is_ready=FALSE")
    print("Reason: Initial purchase intent needs price exposure first")
    print()
    
    sender_id = "test_initial_intent"
    clear_conversation(sender_id)
    
    # Test the exact failing scenario
    message = "I want to buy Wild Stone perfume"
    print(f"👤 Customer: {message}")
    
    response = send_message(sender_id, message)
    
    if response:
        print(f"🤖 Agent: {response.get('response_text', 'No response')[:200]}...")
        print(f"🛍️  Products: {response.get('product_interested', 'None')}")
        
        # Get product IDs if available
        product_ids = response.get('interested_product_ids', [])
        print(f"🆔 Product IDs: {len(product_ids)} IDs: {product_ids}")
        
        is_ready = response.get('is_ready', False)
        print(f"🚀 Ready for Handover: {is_ready}")
        
        print("\n📊 TEST ANALYSIS:")
        if is_ready:
            print("❌ FAIL: is_ready=True (should be False for initial intent)")
            print("   Issue: Customer expressed initial purchase intent")
            print("   Expected: Show prices first, then get confirmation")
            return False
        else:
            print("✅ PASS: is_ready=False (correct for initial intent)")
            print("   Correct: Customer needs to see prices before confirmation")
            return True
    else:
        print("❌ FAIL: No response from API")
        return False

def test_purchase_progression():
    """Test the full progression from intent to confirmation"""
    print("\n🔄 PROGRESSION TEST: Intent → Prices → Confirmation")
    print("=" * 70)
    
    sender_id = "test_progression"
    clear_conversation(sender_id)
    
    # Step 1: Initial intent (should be FALSE)
    print("📍 Step 1: Initial Purchase Intent")
    response1 = send_message(sender_id, "I want to buy Wild Stone perfume")
    if response1:
        is_ready1 = response1.get('is_ready', False)
        print(f"   is_ready: {is_ready1} (should be False)")
        
        # Check if agent mentions prices
        response_text = response1.get('response_text', '').lower()
        mentions_price = any(word in response_text for word in ['price', 'cost', '৳', 'taka'])
        print(f"   Mentions price: {mentions_price}")
    
    time.sleep(1)
    
    # Step 2: Ask for price (should be FALSE)
    print("\n📍 Step 2: Price Inquiry")
    response2 = send_message(sender_id, "What's the price?")
    if response2:
        is_ready2 = response2.get('is_ready', False)
        print(f"   is_ready: {is_ready2} (should be False)")
    
    time.sleep(1)
    
    # Step 3: Confirm after seeing price (should be TRUE)
    print("\n📍 Step 3: Purchase Confirmation")
    response3 = send_message(sender_id, "Yes, I'll take it")
    if response3:
        is_ready3 = response3.get('is_ready', False)
        print(f"   is_ready: {is_ready3} (should be True)")
        
        if is_ready3:
            print("✅ SUCCESS: Proper progression - ready after confirmation")
        else:
            print("❌ ISSUE: Should be ready after explicit confirmation")

def test_various_intent_phrases():
    """Test different ways of expressing initial purchase intent"""
    print("\n🧪 PHRASE TESTING: Various Initial Purchase Intents")
    print("=" * 70)
    print("All of these should be is_ready=FALSE (need price exposure first)")
    print()
    
    test_phrases = [
        "I want to buy Wild Stone perfume",
        "I want to purchase this perfume",
        "I need to buy a perfume",
        "I want to order Wild Stone perfume",
        "I'm looking to buy perfume"
    ]
    
    results = []
    
    for i, phrase in enumerate(test_phrases, 1):
        sender_id = f"test_phrase_{i}"
        clear_conversation(sender_id)
        
        print(f"🧪 Test {i}: '{phrase}'")
        response = send_message(sender_id, phrase)
        
        if response:
            is_ready = response.get('is_ready', False)
            status = "❌ FAIL" if is_ready else "✅ PASS"
            print(f"   {status}: is_ready={is_ready}")
            results.append(not is_ready)  # True if correct (False is_ready)
        else:
            print("   ❌ FAIL: No response")
            results.append(False)
        
        time.sleep(0.5)
    
    success_rate = sum(results) / len(results) * 100
    print(f"\n📊 Initial Intent Detection Success Rate: {success_rate:.1f}%")
    return success_rate == 100.0

if __name__ == "__main__":
    print("🚀 FOCUSED TEST: Initial Purchase Intent vs Confirmation")
    print("🎯 Objective: Fix 'I want to buy X' being marked as ready=True")
    print("=" * 80)
    
    if not test_api_health():
        print("❌ Cannot proceed - API not available")
        exit(1)
    
    print()
    
    # Run focused tests
    test1_pass = test_initial_purchase_intent()
    print()
    
    test_purchase_progression()
    print()
    
    test2_pass = test_various_intent_phrases()
    
    print("\n" + "=" * 80)
    print("🏁 FOCUSED TEST SUMMARY")
    print("=" * 80)
    
    if test1_pass and test2_pass:
        print("✅ SUCCESS: Initial purchase intent detection fixed!")
        print("   'I want to buy X' now correctly triggers is_ready=FALSE")
        print("   System properly distinguishes intent from confirmation")
    else:
        print("❌ ISSUES REMAIN: Initial purchase intent still problematic")
        print("   Need further refinement of purchase detection logic")
    
    print("\n🔧 Next Steps:")
    print("   1. If tests pass: Run full end-to-end test")
    print("   2. If tests fail: Review and adjust explicit purchase detection")
