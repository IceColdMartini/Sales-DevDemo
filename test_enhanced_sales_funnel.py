#!/usr/bin/env python3
"""
Test Enhanced Sales Funnel with Proper Price Introduction and Purchase Confirmation
"""

import requests
import time
import json

# API Configuration
API_BASE_URL = "http://localhost:8000"
WEBHOOK_URL = f"{API_BASE_URL}/api/webhook"

def send_message(sender_id: str, message: str) -> dict:
    """Send a message to the sales agent"""
    payload = {
        "sender": sender_id,
        "recipient": "page_123",
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
        response.raise_for_status()
        print(f"🗑️  Cleared conversation for {sender_id}")
    except Exception as e:
        print(f"❌ Failed to clear conversation: {e}")

def test_proper_sales_funnel_with_prices():
    """Test the complete sales funnel with mandatory price introduction"""
    print("\n🏗️  ENHANCED SALES FUNNEL TEST WITH PRICE INTRODUCTION")
    print("=" * 80)
    print("Testing that is_ready=true only occurs after:")
    print("1. Customer sees product prices")
    print("2. Customer explicitly confirms purchase")
    print("3. Proper handling of multiple products")
    
    sender_id = "test_enhanced_sales_funnel"
    clear_conversation(sender_id)
    
    # Stage 1: Initial Interest
    print("\n📍 STAGE 1: Initial Interest")
    print("-" * 50)
    
    message = "Hi, I'm interested in perfumes and face wash"
    print(f"👤 Customer: {message}")
    response = send_message(sender_id, message)
    
    if response:
        print(f"🤖 Agent: {response.get('response_text', 'No response')[:200]}...")
        print(f"🛍️  Product Interest: {response.get('product_interested', 'None')}")
        print(f"🚀 Ready to Buy: {response.get('is_ready', False)} ← Should be FALSE")
        
        if response.get('is_ready'):
            print("❌ ERROR: Customer marked ready at initial interest stage!")
        else:
            print("✅ CORRECT: Not ready at initial interest stage")
    
    time.sleep(2)
    
    # Stage 2: Product Inquiry
    print("\n📍 STAGE 2: Specific Product Inquiry")
    print("-" * 50)
    
    message = "Tell me about the Wild Stone perfume and Himalaya neem face wash"
    print(f"👤 Customer: {message}")
    response = send_message(sender_id, message)
    
    if response:
        print(f"🤖 Agent: {response.get('response_text', 'No response')[:200]}...")
        print(f"🛍️  Product Interest: {response.get('product_interested', 'None')}")
        print(f"🚀 Ready to Buy: {response.get('is_ready', False)} ← Should be FALSE")
        
        if response.get('is_ready'):
            print("❌ ERROR: Customer marked ready without seeing prices!")
        else:
            print("✅ CORRECT: Not ready without price exposure")
    
    time.sleep(2)
    
    # Stage 3: Price Inquiry - CRITICAL STAGE
    print("\n📍 STAGE 3: Price Inquiry - MANDATORY PRICE EXPOSURE")
    print("-" * 50)
    
    message = "How much do these products cost?"
    print(f"👤 Customer: {message}")
    response = send_message(sender_id, message)
    
    if response:
        print(f"🤖 Agent: {response.get('response_text', 'No response')[:300]}...")
        print(f"🛍️  Product Interest: {response.get('product_interested', 'None')}")
        print(f"🚀 Ready to Buy: {response.get('is_ready', False)} ← Should be FALSE")
        
        # Check if prices are mentioned in response
        response_text = response.get('response_text', '')
        has_price_symbols = any(symbol in response_text for symbol in ['₹', 'Rs', 'price', 'cost'])
        
        if has_price_symbols:
            print("✅ GOOD: Agent provided pricing information")
        else:
            print("⚠️  WARNING: Agent should provide clear pricing when asked")
        
        if response.get('is_ready'):
            print("❌ ERROR: Customer marked ready at price inquiry stage!")
        else:
            print("✅ CORRECT: Not ready at price inquiry stage")
    
    time.sleep(2)
    
    # Stage 4: Price Evaluation
    print("\n📍 STAGE 4: Price Evaluation")
    print("-" * 50)
    
    message = "The prices look reasonable. I like both products."
    print(f"👤 Customer: {message}")
    response = send_message(sender_id, message)
    
    if response:
        print(f"🤖 Agent: {response.get('response_text', 'No response')[:200]}...")
        print(f"🛍️  Product Interest: {response.get('product_interested', 'None')}")
        print(f"🚀 Ready to Buy: {response.get('is_ready', False)} ← Should be FALSE")
        
        if response.get('is_ready'):
            print("❌ ERROR: Customer marked ready without explicit purchase confirmation!")
        else:
            print("✅ CORRECT: Not ready without explicit confirmation")
    
    time.sleep(2)
    
    # Stage 5: Purchase Intent (not confirmation yet)
    print("\n📍 STAGE 5: Purchase Intent - Strong Interest")
    print("-" * 50)
    
    message = "These sound perfect for what I need."
    print(f"👤 Customer: {message}")
    response = send_message(sender_id, message)
    
    if response:
        print(f"🤖 Agent: {response.get('response_text', 'No response')[:200]}...")
        print(f"🛍️  Product Interest: {response.get('product_interested', 'None')}")
        print(f"🚀 Ready to Buy: {response.get('is_ready', False)} ← Should be FALSE")
        
        if response.get('is_ready'):
            print("❌ ERROR: Purchase intent should not trigger readiness!")
        else:
            print("✅ CORRECT: Purchase intent is not purchase confirmation")
    
    time.sleep(2)
    
    # Stage 6: EXPLICIT Purchase Confirmation
    print("\n📍 STAGE 6: EXPLICIT Purchase Confirmation")
    print("-" * 50)
    
    message = "Yes, I want to buy both the Wild Stone perfume and Himalaya neem face wash."
    print(f"👤 Customer: {message}")
    response = send_message(sender_id, message)
    
    if response:
        print(f"🤖 Agent: {response.get('response_text', 'No response')[:200]}...")
        print(f"🛍️  Product Interest: {response.get('product_interested', 'None')}")
        print(f"🚀 Ready to Buy: {response.get('is_ready', False)} ← Should be TRUE")
        
        if response.get('is_ready'):
            print("✅ SUCCESS: Customer is now ready for purchase!")
            
            # Check if multiple products are handled properly
            product_interested = response.get('product_interested', '')
            if product_interested and ('Wild Stone' in product_interested or 'Himalaya' in product_interested):
                print("✅ EXCELLENT: Product interest properly captured")
                if 'Multiple' in product_interested or ',' in product_interested:
                    print("✅ PERFECT: Multiple products handled correctly")
                else:
                    print("⚠️  NOTE: Check if both products are captured")
            else:
                print("⚠️  WARNING: Product interest should be captured")
                
        else:
            print("❌ CRITICAL ERROR: Customer explicitly confirmed purchase but not marked ready!")
    
    print("\n" + "="*80)
    print("🎯 SALES FUNNEL TEST SUMMARY:")
    print("✓ Stages 1-5: is_ready should be FALSE")
    print("✓ Stage 6: is_ready should be TRUE only after explicit confirmation")
    print("✓ Price introduction: Must happen before purchase confirmation")
    print("✓ Multiple products: Should be handled properly")
    return response

def test_multiple_product_scenarios():
    """Test different multiple product scenarios"""
    print("\n🛍️  MULTIPLE PRODUCT SCENARIOS TEST")
    print("=" * 60)
    
    scenarios = [
        {
            "name": "Mixed Categories",
            "sender": "test_mixed_products",
            "messages": [
                "I need skincare and fragrance products",
                "Show me face wash and perfumes",
                "What are the prices for these?",
                "I'll take the neem face wash and Wild Stone perfume"
            ]
        },
        {
            "name": "Budget Constraint",
            "sender": "test_budget_products", 
            "messages": [
                "I want beauty products under ₹500",
                "Show me options in my budget",
                "What exactly costs how much?",
                "Yes, I want to buy the products within my budget"
            ]
        }
    ]
    
    for scenario in scenarios:
        print(f"\n📋 Testing: {scenario['name']}")
        print("-" * 40)
        
        clear_conversation(scenario['sender'])
        
        for i, message in enumerate(scenario['messages'], 1):
            print(f"\n👤 Step {i}: {message}")
            response = send_message(scenario['sender'], message)
            
            if response:
                print(f"🤖 Response: {response.get('response_text', 'No response')[:150]}...")
                print(f"🛍️  Products: {response.get('product_interested', 'None')}")
                print(f"🚀 Ready: {response.get('is_ready', False)}")
                
                # Only the last message should potentially trigger readiness
                expected_ready = (i == len(scenario['messages']))
                if response.get('is_ready') and not expected_ready:
                    print(f"⚠️  WARNING: Ready too early at step {i}")
                elif not response.get('is_ready') and expected_ready:
                    print(f"❌ ERROR: Should be ready at final confirmation step")
                else:
                    print("✅ Correct readiness status")
            
            time.sleep(1)

def test_price_range_filtering():
    """Test price range filtering functionality"""
    print("\n💰 PRICE RANGE FILTERING TEST")
    print("=" * 50)
    
    sender_id = "test_price_filtering"
    clear_conversation(sender_id)
    
    # Test price range specification
    message = "I want skincare products under ₹200"
    print(f"👤 Customer: {message}")
    response = send_message(sender_id, message)
    
    if response:
        print(f"🤖 Agent: {response.get('response_text', 'No response')[:200]}...")
        
        # Check if agent acknowledges the budget constraint
        response_text = response.get('response_text', '').lower()
        budget_acknowledged = any(word in response_text for word in ['budget', '200', 'under', 'affordable', 'within'])
        
        if budget_acknowledged:
            print("✅ GOOD: Agent acknowledged budget constraint")
        else:
            print("⚠️  WARNING: Agent should acknowledge customer's budget")

if __name__ == "__main__":
    print("🚀 Starting Enhanced Sales Funnel Testing")
    print("Testing proper price introduction and purchase confirmation logic")
    
    # Test 1: Main sales funnel with prices
    test_proper_sales_funnel_with_prices()
    
    # Test 2: Multiple product scenarios
    test_multiple_product_scenarios()
    
    # Test 3: Price range filtering
    test_price_range_filtering()
    
    print("\n🏁 Enhanced Sales Funnel Testing Complete!")
    print("\nKey Validation Points:")
    print("✓ is_ready=true only after explicit purchase confirmation")
    print("✓ Prices must be shown before purchase readiness") 
    print("✓ Multiple products handled correctly")
    print("✓ Price range filtering works")
    print("✓ Proper sales stage progression")
