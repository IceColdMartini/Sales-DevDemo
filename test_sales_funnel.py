#!/usr/bin/env python3
"""
Test script for the enhanced sales funnel system
Tests proper staging and purchase readiness detection
"""

import requests
import time
import json
from typing import Dict, List

# API Configuration
API_BASE_URL = "http://localhost:8000"
WEBHOOK_URL = f"{API_BASE_URL}/api/webhook"

def send_message(sender_id: str, message: str) -> Dict:
    """Send a message to the sales agent"""
    payload = {
        "sender": sender_id,
        "recipient": "page_456",
        "text": message
    }
    
    try:
        response = requests.post(WEBHOOK_URL, json=payload)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"❌ Failed to send message: {e}")
        return {}

def clear_conversation(sender_id: str):
    """Clear conversation history for a user"""
    try:
        response = requests.delete(f"{API_BASE_URL}/api/webhook/conversation/{sender_id}")
        response.raise_for_status()
        print(f"🗑️  Cleared conversation for {sender_id}")
    except Exception as e:
        print(f"❌ Failed to clear conversation: {e}")

def test_proper_sales_funnel():
    """Test the complete sales funnel with proper staging"""
    print("\n🎯 Testing Proper Sales Funnel - Should NOT be ready until explicit confirmation")
    print("=" * 80)
    
    sender_id = "test_sales_funnel"
    clear_conversation(sender_id)
    
    # Stage 1: Interest Exploration
    print("\n📍 STAGE 1: Interest Exploration")
    print("-" * 40)
    
    message = "Hi, I'm looking for a good perfume"
    print(f"👤 Customer: {message}")
    response = send_message(sender_id, message)
    
    if response:
        print(f"🤖 Agent: {response.get('response_text', 'No response')}")
        print(f"📦 Product Interest: {response.get('product_interested', 'None')}")
        print(f"🎯 Ready Status: {response.get('is_ready', False)} (Should be FALSE)")
        
        if response.get('is_ready'):
            print("❌ ERROR: is_ready should be FALSE at interest exploration stage!")
        else:
            print("✅ CORRECT: Not ready at exploration stage")
    
    time.sleep(2)
    
    # Stage 2: Product Selection
    print("\n📍 STAGE 2: Product Selection")
    print("-" * 40)
    
    message = "Tell me more about that Wild Stone perfume"
    print(f"👤 Customer: {message}")
    response = send_message(sender_id, message)
    
    if response:
        print(f"🤖 Agent: {response.get('response_text', 'No response')}")
        print(f"📦 Product Interest: {response.get('product_interested', 'None')}")
        print(f"🎯 Ready Status: {response.get('is_ready', False)} (Should be FALSE)")
        
        if response.get('is_ready'):
            print("❌ ERROR: is_ready should be FALSE at product selection stage!")
        else:
            print("✅ CORRECT: Not ready at selection stage")
    
    time.sleep(2)
    
    # Stage 3: Price Inquiry
    print("\n📍 STAGE 3: Price Inquiry")
    print("-" * 40)
    
    message = "How much does it cost?"
    print(f"👤 Customer: {message}")
    response = send_message(sender_id, message)
    
    if response:
        print(f"🤖 Agent: {response.get('response_text', 'No response')}")
        print(f"📦 Product Interest: {response.get('product_interested', 'None')}")
        print(f"🎯 Ready Status: {response.get('is_ready', False)} (Should be FALSE)")
        
        # Check if price is mentioned in response
        if "₹" in response.get('response_text', ''):
            print("✅ GOOD: Price mentioned in response")
        else:
            print("⚠️  WARNING: Price should be mentioned when customer asks about cost")
        
        if response.get('is_ready'):
            print("❌ ERROR: is_ready should be FALSE at price inquiry stage!")
        else:
            print("✅ CORRECT: Not ready at price inquiry stage")
    
    time.sleep(2)
    
    # Stage 4: Price Evaluation (ambiguous response)
    print("\n📍 STAGE 4: Price Evaluation - Ambiguous Response")
    print("-" * 40)
    
    message = "That's a bit expensive"
    print(f"👤 Customer: {message}")
    response = send_message(sender_id, message)
    
    if response:
        print(f"🤖 Agent: {response.get('response_text', 'No response')}")
        print(f"📦 Product Interest: {response.get('product_interested', 'None')}")
        print(f"🎯 Ready Status: {response.get('is_ready', False)} (Should be FALSE)")
        
        if response.get('is_ready'):
            print("❌ ERROR: is_ready should be FALSE when customer has price concerns!")
        else:
            print("✅ CORRECT: Not ready when customer expresses price concerns")
    
    time.sleep(2)
    
    # Stage 5: Explicit Purchase Confirmation
    print("\n📍 STAGE 5: Explicit Purchase Confirmation")
    print("-" * 40)
    
    message = "Actually, it's worth it. Yes, I want to buy it."
    print(f"👤 Customer: {message}")
    response = send_message(sender_id, message)
    
    if response:
        print(f"🤖 Agent: {response.get('response_text', 'No response')}")
        print(f"📦 Product Interest: {response.get('product_interested', 'None')}")
        print(f"🎯 Ready Status: {response.get('is_ready', False)} (Should be TRUE)")
        
        if response.get('is_ready'):
            print("✅ EXCELLENT: Now ready after explicit purchase confirmation!")
        else:
            print("❌ ERROR: Should be ready after explicit purchase confirmation!")

def test_price_range_filtering():
    """Test price range filtering functionality"""
    print("\n💰 Testing Price Range Filtering")
    print("=" * 50)
    
    sender_id = "test_price_range"
    clear_conversation(sender_id)
    
    message = "I need a perfume under ₹300"
    print(f"👤 Customer: {message}")
    response = send_message(sender_id, message)
    
    if response:
        print(f"🤖 Agent: {response.get('response_text', 'No response')}")
        print(f"📦 Product Interest: {response.get('product_interested', 'None')}")
        print(f"🎯 Ready Status: {response.get('is_ready', False)} (Should be FALSE)")
        
        # Check if agent mentions price range consideration
        response_text = response.get('response_text', '').lower()
        if "₹300" in response_text or "under" in response_text or "budget" in response_text:
            print("✅ GOOD: Agent acknowledges price range")
        else:
            print("⚠️  WARNING: Agent should acknowledge customer's price range")

def test_multiple_products():
    """Test handling of multiple products interest"""
    print("\n🛍️  Testing Multiple Products Interest")
    print("=" * 50)
    
    sender_id = "test_multiple"
    clear_conversation(sender_id)
    
    message = "I need perfume and also something for my hair"
    print(f"👤 Customer: {message}")
    response = send_message(sender_id, message)
    
    if response:
        print(f"🤖 Agent: {response.get('response_text', 'No response')}")
        print(f"📦 Product Interest: {response.get('product_interested', 'None')}")
        print(f"🎯 Ready Status: {response.get('is_ready', False)} (Should be FALSE)")
        
        product_interest = response.get('product_interested', '')
        if ',' in product_interest or 'multiple' in product_interest.lower():
            print("✅ GOOD: Multiple products detected")
        else:
            print("⚠️  INFO: Single product focus (also acceptable)")

def test_premature_ready_prevention():
    """Test that system doesn't mark ready prematurely"""
    print("\n🚫 Testing Premature Ready Prevention")
    print("=" * 50)
    
    test_cases = [
        "I like that perfume",
        "That sounds good",
        "Interesting, tell me more",
        "I'm thinking about it",
        "Maybe I'll consider it"
    ]
    
    for i, message in enumerate(test_cases, 1):
        sender_id = f"test_premature_{i}"
        clear_conversation(sender_id)
        
        print(f"\n🧪 Test {i}: '{message}'")
        response = send_message(sender_id, message)
        
        if response:
            is_ready = response.get('is_ready', False)
            if is_ready:
                print(f"❌ ERROR: Should NOT be ready for: '{message}'")
            else:
                print(f"✅ CORRECT: Not ready for: '{message}'")

def run_sales_funnel_tests():
    """Run all sales funnel tests"""
    print("🚀 Starting Enhanced Sales Funnel Testing")
    print("=" * 80)
    
    # Test health first
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        if response.status_code == 200:
            print("✅ API is healthy")
        else:
            print("❌ API health check failed")
            return
    except Exception as e:
        print(f"❌ Cannot connect to API: {e}")
        return
    
    # Run comprehensive tests
    test_proper_sales_funnel()
    test_price_range_filtering()
    test_multiple_products()
    test_premature_ready_prevention()
    
    print("\n" + "=" * 80)
    print("🎉 Sales Funnel Testing Complete!")
    print("\nKey Features Tested:")
    print("✅ Proper sales staging (interest → selection → pricing → confirmation)")
    print("✅ Price discussion before readiness")
    print("✅ Explicit purchase confirmation required")
    print("✅ Price range filtering")
    print("✅ Multiple products handling")
    print("✅ Prevention of premature readiness")

if __name__ == "__main__":
    run_sales_funnel_tests()
