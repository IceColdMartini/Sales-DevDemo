#!/usr/bin/env python3
"""
Targeted test for is_ready flag behavior analysis
"""
import requests
import json
import time

API_BASE_URL = "http://localhost:8000"
WEBHOOK_URL = f"{API_BASE_URL}/api/webhook"

def send_message(sender_id: str, message: str) -> dict:
    payload = {"sender": sender_id, "recipient": "page_123", "text": message}
    try:
        response = requests.post(WEBHOOK_URL, json=payload, timeout=30)
        return response.json() if response.status_code == 200 else {"error": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"error": str(e)}

def clear_conversation(sender_id: str):
    try:
        requests.delete(f"{API_BASE_URL}/api/webhook/conversation/{sender_id}")
    except:
        pass

def test_is_ready_flag_behavior():
    print("🔍 TARGETED is_ready FLAG BEHAVIOR TEST")
    print("=" * 60)
    
    test_cases = [
        ("I'm looking for perfume", "Interest expression"),
        ("I need Wild Stone perfume", "Specific product need"),
        ("Show me the Wild Stone perfume", "Product inquiry"),
        ("How much does Wild Stone perfume cost?", "Price inquiry"),
        ("I want to buy Wild Stone perfume", "Purchase intent"),
        ("Yes, I'll take the Wild Stone perfume", "Explicit confirmation"),
        ("I'll buy it", "Short confirmation"),
    ]
    
    for i, (message, description) in enumerate(test_cases, 1):
        print(f"\n🧪 Test {i}: {description}")
        sender_id = f"test_ready_{i}"
        clear_conversation(sender_id)
        
        response = send_message(sender_id, message)
        
        if "error" not in response:
            is_ready = response.get('is_ready', False)
            product_ids = response.get('interested_product_ids', [])
            product_interested = response.get('product_interested', '')
            
            print(f"   Message: \"{message}\"")
            print(f"   is_ready: {is_ready}")
            print(f"   Products: {len(product_ids)} - {product_interested}")
            print(f"   Expected: Should be False until explicit purchase confirmation")
            
            status = "✅ CORRECT" if not is_ready or "buy" in message.lower() or "take" in message.lower() else "❌ TOO EAGER"
            print(f"   Status: {status}")
        else:
            print(f"   ❌ Error: {response['error']}")
        
        time.sleep(1)

if __name__ == "__main__":
    test_is_ready_flag_behavior()
