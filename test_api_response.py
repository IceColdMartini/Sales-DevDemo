#!/usr/bin/env python3
"""
Test the API response format to verify it includes all required fields for Routing Agent
"""

import requests
import json

API_BASE_URL = "http://localhost:8000"
WEBHOOK_URL = f"{API_BASE_URL}/api/webhook"

def test_api_response_format():
    """Test that API response includes all required fields for Routing Agent"""
    print("🧪 Testing API Response Format for Routing Agent Integration")
    print("=" * 70)
    
    # Clear conversation
    try:
        requests.delete(f"{API_BASE_URL}/api/webhook/conversation/test_api_response")
    except:
        pass
    
    # Send a purchase confirmation message
    payload = {
        "sender": "test_api_response",
        "recipient": "page_123",
        "text": "I'll take the Wild Stone perfume"
    }
    
    try:
        response = requests.post(WEBHOOK_URL, json=payload, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            print("📦 API Response Structure:")
            print(json.dumps(data, indent=2))
            
            print("\n🔍 Field Validation:")
            
            # Check required fields
            required_fields = ["sender", "response_text", "is_ready"]
            for field in required_fields:
                if field in data:
                    print(f"✅ {field}: {type(data[field]).__name__} = {data[field] if field != 'response_text' else 'Content present'}")
                else:
                    print(f"❌ {field}: MISSING")
            
            # Check optional fields
            optional_fields = ["product_interested", "interested_product_ids"]
            for field in optional_fields:
                if field in data:
                    print(f"✅ {field}: {type(data[field]).__name__} = {data[field]}")
                else:
                    print(f"⚠️  {field}: Not present")
            
            print("\n🎯 Routing Agent Integration Readiness:")
            print(f"• User ID: {data.get('sender')}")
            print(f"• Response Message: {'✅ Present' if data.get('response_text') else '❌ Missing'}")
            print(f"• Product Names: {data.get('product_interested', 'None')}")
            print(f"• Product IDs: {data.get('interested_product_ids', 'None')}")
            print(f"• Ready for Handover: {data.get('is_ready', False)}")
            
            if data.get('is_ready'):
                print("\n🚀 HANDOVER READY: This conversation should be passed to the next agent!")
            else:
                print("\n🔄 CONTINUE: Keep sending messages to Sales Agent")
                
        else:
            print(f"❌ API Error: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Test Failed: {e}")

if __name__ == "__main__":
    test_api_response_format()
