#!/usr/bin/env python3
"""
Comprehensive test for the enhanced sales funnel system
Tests proper staging, price handling, and purchase readiness detection
"""
import requests
import time
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
        response = requests.post(WEBHOOK_URL, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"❌ Failed to send message: {e}")
        return {}

def clear_conversation(sender_id: str):
    """Clear conversation history for a user"""
    try:
        response = requests.delete(f"{API_BASE_URL}/api/webhook/conversation/{sender_id}")
        if response.status_code == 200:
            print(f"🗑️  Cleared conversation for {sender_id}")
        else:
            print(f"⚠️  Could not clear conversation for {sender_id}")
    except Exception as e:
        print(f"❌ Failed to clear conversation: {e}")

def test_proper_sales_funnel():
    """Test the complete sales funnel - should NOT be ready until explicit confirmation"""
    print("\n🎯 ENHANCED SALES FUNNEL TEST")
    print("=" * 80)
    print("Testing that is_ready=true only occurs after explicit purchase confirmation")
    
    sender_id = "test_enhanced_funnel"
    clear_conversation(sender_id)
    
    # Stage 1: Initial Interest
    print("\n📍 STAGE 1: Initial Interest Exploration")
    print("-" * 50)
    
    message = "Hi, I'm looking for a good perfume"
    print(f"👤 Customer: {message}")
    response = send_message(sender_id, message)
    
    if response:
        print(f"🤖 Agent: {response.get('response_text', 'No response')[:150]}...")
        print(f"🛍️  Product Interest: {response.get('product_interested', 'None')}")
        print(f"🚀 Ready to Buy: {response.get('is_ready', False)} ← Should be FALSE")
        
        if response.get('is_ready'):
            print("❌ ERROR: Customer is marked ready too early!")
        else:
            print("✅ CORRECT: Customer not ready yet")
    
    time.sleep(2)
    
    # Stage 2: Product Exploration
    print("\n📍 STAGE 2: Product Discovery")
    print("-" * 50)
    
    message = "Tell me more about that Wild Stone perfume"
    print(f"👤 Customer: {message}")
    response = send_message(sender_id, message)
    
    if response:
        print(f"🤖 Agent: {response.get('response_text', 'No response')[:150]}...")
        print(f"🛍️  Product Interest: {response.get('product_interested', 'None')}")
        print(f"🚀 Ready to Buy: {response.get('is_ready', False)} ← Should be FALSE")
        
        if response.get('is_ready'):
            print("❌ ERROR: Customer is marked ready too early!")
        else:
            print("✅ CORRECT: Customer still exploring")
    
    time.sleep(2)
    
    # Stage 3: Price Inquiry
    print("\n📍 STAGE 3: Price Inquiry")
    print("-" * 50)
    
    message = "How much does it cost?"
    print(f"👤 Customer: {message}")
    response = send_message(sender_id, message)
    
    if response:
        print(f"🤖 Agent: {response.get('response_text', 'No response')[:150]}...")
        print(f"🛍️  Product Interest: {response.get('product_interested', 'None')}")
        print(f"🚀 Ready to Buy: {response.get('is_ready', False)} ← Should be FALSE")
        
        if response.get('is_ready'):
            print("❌ ERROR: Customer is marked ready too early!")
        else:
            print("✅ CORRECT: Price inquiry doesn't mean ready to buy")
    
    time.sleep(2)
    
    # Stage 4: Price Evaluation (Neutral Response)
    print("\n📍 STAGE 4: Price Evaluation - Neutral Response")
    print("-" * 50)
    
    message = "That's a bit expensive, but let me think about it"
    print(f"👤 Customer: {message}")
    response = send_message(sender_id, message)
    
    if response:
        print(f"🤖 Agent: {response.get('response_text', 'No response')[:150]}...")
        print(f"🛍️  Product Interest: {response.get('product_interested', 'None')}")
        print(f"🚀 Ready to Buy: {response.get('is_ready', False)} ← Should be FALSE")
        
        if response.get('is_ready'):
            print("❌ ERROR: Customer expressed hesitation but marked ready!")
        else:
            print("✅ CORRECT: Customer is considering, not ready yet")
    
    time.sleep(2)
    
    # Stage 5: Explicit Purchase Confirmation
    print("\n📍 STAGE 5: Explicit Purchase Confirmation")
    print("-" * 50)
    
    message = "You know what, it's worth it. Yes, I want to buy the Wild Stone perfume."
    print(f"👤 Customer: {message}")
    response = send_message(sender_id, message)
    
    if response:
        print(f"🤖 Agent: {response.get('response_text', 'No response')[:150]}...")
        print(f"🛍️  Product Interest: {response.get('product_interested', 'None')}")
        print(f"🚀 Ready to Buy: {response.get('is_ready', False)} ← Should be TRUE")
        
        if response.get('is_ready'):
            print("✅ CORRECT: Customer explicitly confirmed purchase!")
        else:
            print("❌ ERROR: Customer confirmed purchase but not marked ready!")
    
    print("\n" + "="*80)

def test_price_range_filtering():
    """Test price range filtering functionality"""
    print("\n💰 PRICE RANGE FILTERING TEST")
    print("=" * 60)
    
    sender_id = "test_price_range"
    clear_conversation(sender_id)
    
    message = "I need a good perfume under ₹300"
    print(f"👤 Customer: {message}")
    response = send_message(sender_id, message)
    
    if response:
        print(f"🤖 Agent: {response.get('response_text', 'No response')[:200]}...")
        print(f"🛍️  Product Interest: {response.get('product_interested', 'None')}")
        print(f"🚀 Ready to Buy: {response.get('is_ready', False)}")
        print("📊 Analysis: Should suggest products under ₹300 only")
    
    time.sleep(2)

def test_multiple_products_interest():
    """Test handling customers interested in multiple products"""
    print("\n🛍️  MULTIPLE PRODUCTS TEST")
    print("=" * 60)
    
    sender_id = "test_multiple"
    clear_conversation(sender_id)
    
    # Step 1: Interest in multiple product types
    message = "I need a good shampoo and also looking for a nice perfume"
    print(f"👤 Customer: {message}")
    response = send_message(sender_id, message)
    
    if response:
        print(f"🤖 Agent: {response.get('response_text', 'No response')[:150]}...")
        print(f"🛍️  Product Interest: {response.get('product_interested', 'None')}")
        print(f"🚀 Ready to Buy: {response.get('is_ready', False)} ← Should be FALSE")
    
    time.sleep(2)
    
    # Step 2: Focus on specific products
    message = "Tell me about the Garnier shampoo and Wild Stone perfume prices"
    print(f"👤 Customer: {message}")
    response = send_message(sender_id, message)
    
    if response:
        print(f"🤖 Agent: {response.get('response_text', 'No response')[:150]}...")
        print(f"🛍️  Product Interest: {response.get('product_interested', 'None')}")
        print(f"🚀 Ready to Buy: {response.get('is_ready', False)} ← Should be FALSE")
    
    time.sleep(2)
    
    # Step 3: Purchase decision for multiple products
    message = "Perfect! I'll take both the Garnier shampoo and Wild Stone perfume"
    print(f"👤 Customer: {message}")
    response = send_message(sender_id, message)
    
    if response:
        print(f"🤖 Agent: {response.get('response_text', 'No response')[:150]}...")
        print(f"🛍️  Product Interest: {response.get('product_interested', 'None')}")
        print(f"🚀 Ready to Buy: {response.get('is_ready', False)} ← Should be TRUE")
        
        if response.get('is_ready'):
            print("✅ CORRECT: Multiple product purchase confirmed!")
        else:
            print("❌ ERROR: Multiple product purchase not detected!")

def test_objection_handling():
    """Test how objections are handled without premature readiness"""
    print("\n🤔 OBJECTION HANDLING TEST")
    print("=" * 60)
    
    sender_id = "test_objections"
    clear_conversation(sender_id)
    
    # Build up interest
    send_message(sender_id, "I want a good perfume")
    time.sleep(1)
    
    # Price objection
    message = "₹450 is too expensive for me"
    print(f"👤 Customer: {message}")
    response = send_message(sender_id, message)
    
    if response:
        print(f"🤖 Agent: {response.get('response_text', 'No response')[:150]}...")
        print(f"🛍️  Product Interest: {response.get('product_interested', 'None')}")
        print(f"🚀 Ready to Buy: {response.get('is_ready', False)} ← Should be FALSE")
        print("📊 Analysis: Should handle objection and suggest alternatives")
        
        if response.get('is_ready'):
            print("❌ ERROR: Price objection should not mark customer as ready!")
        else:
            print("✅ CORRECT: Objection handled, customer not marked ready")

def run_enhanced_sales_tests():
    """Run all enhanced sales funnel tests"""
    print("🚀 ENHANCED SALES FUNNEL TESTING")
    print("=" * 80)
    print("Testing the new LLM-based sales stage analysis system")
    print("Key Requirements:")
    print("- Only set is_ready=true after explicit purchase confirmation")
    print("- Handle price ranges and budget constraints")
    print("- Support multiple product interests")
    print("- Properly introduce prices at the right stage")
    print("- Handle objections without premature readiness")
    print("=" * 80)
    
    # Check API health
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ API is healthy, starting tests...")
        else:
            print("❌ API health check failed")
            return
    except Exception as e:
        print(f"❌ Cannot connect to API: {e}")
        return
    
    # Run test suite
    test_proper_sales_funnel()
    test_price_range_filtering()
    test_multiple_products_interest()
    test_objection_handling()
    
    print("\n🎉 TESTING COMPLETE!")
    print("\n📋 SUMMARY OF EXPECTATIONS:")
    print("✅ is_ready should only be true after explicit purchase confirmation")
    print("✅ Price ranges should filter product suggestions appropriately")
    print("✅ Multiple products should be handled correctly")
    print("✅ Objections should not trigger premature readiness")
    print("✅ Prices should be introduced naturally in the conversation")

if __name__ == "__main__":
    run_enhanced_sales_tests()
