#!/usr/bin/env python3

import requests
import json
import time

# Test configuration
BASE_URL = "http://localhost:8000"
HEADERS = {"Content-Type": "application/json"}

def test_health_check():
    """Test basic health check"""
    print("🔄 Testing health check...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"✅ Health check: {response.status_code}")
        print(f"📊 Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_webhook_perfume_inquiry():
    """Test webhook with perfume inquiry"""
    print("\n🔄 Testing perfume inquiry...")
    
    payload = {
        "sender": "test_user_123",
        "recipient": "page_456",
        "text": "I'm looking for a good perfume for men"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/webhook", headers=HEADERS, data=json.dumps(payload))
        print(f"✅ Perfume inquiry: {response.status_code}")
        print(f"📝 Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Perfume inquiry failed: {e}")
        return False

def test_webhook_follow_up():
    """Test follow-up message from same user"""
    print("\n🔄 Testing follow-up conversation...")
    
    payload = {
        "sender": "test_user_123", 
        "recipient": "page_456",
        "text": "Tell me more about the Wild Stone perfume"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/webhook", headers=HEADERS, data=json.dumps(payload))
        print(f"✅ Follow-up: {response.status_code}")
        print(f"📝 Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Follow-up failed: {e}")
        return False

def test_webhook_purchase_intent():
    """Test purchase intent detection"""
    print("\n🔄 Testing purchase intent...")
    
    payload = {
        "sender": "test_user_123",
        "recipient": "page_456", 
        "text": "I want to buy this perfume. How can I purchase it?"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/webhook", headers=HEADERS, data=json.dumps(payload))
        print(f"✅ Purchase intent: {response.status_code}")
        print(f"📝 Response: {json.dumps(response.json(), indent=2)}")
        
        response_data = response.json()
        if response_data.get('isReady'):
            print("🎉 Customer is ready to purchase! Handover triggered.")
        else:
            print("⏳ Customer not ready yet, continuing conversation.")
            
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Purchase intent test failed: {e}")
        return False

def test_different_product_inquiry():
    """Test different product type inquiry"""
    print("\n🔄 Testing headphones inquiry...")
    
    payload = {
        "sender": "test_user_456",
        "recipient": "page_456",
        "text": "Do you have any wireless headphones?"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/webhook", headers=HEADERS, data=json.dumps(payload))
        print(f"✅ Headphones inquiry: {response.status_code}")
        print(f"📝 Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Headphones inquiry failed: {e}")
        return False

def test_conversation_status():
    """Test conversation status endpoint"""
    print("\n🔄 Testing conversation status...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/webhook/status/test_user_123")
        print(f"✅ Conversation status: {response.status_code}")
        print(f"📊 Status: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Conversation status failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting Sales Agent API Tests\n")
    
    tests = [
        ("Health Check", test_health_check),
        ("Perfume Inquiry", test_webhook_perfume_inquiry),  
        ("Follow-up Conversation", test_webhook_follow_up),
        ("Purchase Intent", test_webhook_purchase_intent),
        ("Different Product", test_different_product_inquiry),
        ("Conversation Status", test_conversation_status)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"Running: {test_name}")
        print('='*50)
        
        success = test_func()
        results.append((test_name, success))
        
        # Small delay between tests
        time.sleep(1)
    
    # Summary
    print(f"\n{'='*50}")
    print("🏁 TEST SUMMARY")
    print('='*50)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\nResult: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Your Sales Agent is working perfectly!")
    else:
        print("⚠️  Some tests failed. Check the logs above for details.")

if __name__ == "__main__":
    main()
