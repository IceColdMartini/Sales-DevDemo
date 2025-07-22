#!/usr/bin/env python3
"""
Comprehensive end-to-end testing for the Sales Agent API
Tests various conversation scenarios to evaluate LLM responses
"""
import requests
import json
import time
from typing import Dict, List

# API Configuration
API_BASE_URL = "http://localhost:8000"
WEBHOOK_URL = f"{API_BASE_URL}/api/webhook"
HEALTH_URL = f"{API_BASE_URL}/health"

def test_health():
    """Test if the API is healthy"""
    try:
        response = requests.get(HEALTH_URL)
        response.raise_for_status()
        result = response.json()
        print("✅ API Health Check:")
        print(f"   Status: {result['status']}")
        print(f"   PostgreSQL: {result['databases']['postgresql']}")
        print(f"   MongoDB: {result['databases']['mongodb']}")
        print(f"   AI Service: {result['services']['ai_service']}")
        return True
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

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

def test_conversation_scenario(scenario_name: str, sender_id: str, messages: List[str]):
    """Test a complete conversation scenario"""
    print(f"\n🎭 Testing Scenario: {scenario_name}")
    print("=" * 60)
    
    # Clear any existing conversation
    clear_conversation(sender_id)
    
    for i, message in enumerate(messages, 1):
        print(f"\n👤 User [{i}]: {message}")
        
        response = send_message(sender_id, message)
        
        if response:
            print(f"🤖 Agent [{i}]: {response.get('response_text', 'No response')}")
            print(f"📦 Product Interest: {response.get('product_interested', 'None')}")
            print(f"🎯 Ready to Buy: {response.get('is_ready', False)}")
        else:
            print("❌ No response received")
        
        # Add small delay between messages
        time.sleep(1)

def run_comprehensive_tests():
    """Run all test scenarios"""
    print("🚀 Starting Comprehensive Sales Agent Testing")
    print("=" * 60)
    
    # Check API health first
    if not test_health():
        print("❌ API is not healthy. Exiting tests.")
        return
    
    # Test Scenarios
    
    # Scenario 1: Standard Product Inquiry
    test_conversation_scenario(
        "Standard Product Inquiry - Perfume",
        "test_user_001",
        [
            "Hi, I'm looking for a good perfume",
            "I prefer something with a fresh scent",
            "How much does it cost?",
            "Yes, I'd like to purchase it"
        ]
    )
    
    # Scenario 2: Off-topic Conversation Handling
    test_conversation_scenario(
        "Off-topic Conversation Handling",
        "test_user_002", 
        [
            "Hello, I want to buy a body perfume",
            "Can you tell me what we were discussing about?",
            "What's the weather like today?",
            "Actually, let's get back to the perfume discussion"
        ]
    )
    
    # Scenario 3: Multiple Product Categories
    test_conversation_scenario(
        "Multiple Product Categories",
        "test_user_003",
        [
            "I'm interested in beauty products",
            "Show me perfumes and face wash options",
            "Which one would you recommend for oily skin?",
            "I'll take the face wash"
        ]
    )
    
    # Scenario 4: Casual Chat with Product Direction
    test_conversation_scenario(
        "Casual Chat with Product Direction",
        "test_user_004",
        [
            "Hey there! How are you doing?",
            "I had a great day at work today",
            "Tell me what our current conversation is about",
            "That's nice, can you help me find something good for my skin?"
        ]
    )
    
    # Scenario 5: Price Inquiry and Negotiation
    test_conversation_scenario(
        "Price Inquiry and Negotiation",
        "test_user_005",
        [
            "I need a good moisturizer",
            "What's the price range?",
            "That seems expensive. Do you have any discounts?",
            "Okay, I'll consider it"
        ]
    )
    
    # Scenario 6: Comparison Shopping
    test_conversation_scenario(
        "Comparison Shopping",
        "test_user_006",
        [
            "I want to compare different perfumes",
            "What are the differences between your perfume options?",
            "Which one lasts longer?",
            "I'll go with the Wild Stone one"
        ]
    )
    
    # Scenario 7: Specific Brand Request
    test_conversation_scenario(
        "Specific Brand Request",
        "test_user_007",
        [
            "Do you have any Wild Stone products?",
            "I specifically want Wild Stone perfume",
            "Tell me more about its features",
            "Perfect, I want to buy it now"
        ]
    )
    
    # Scenario 8: General Greeting and Product Discovery
    test_conversation_scenario(
        "General Greeting and Product Discovery",
        "test_user_008",
        [
            "Good morning!",
            "I'm just browsing your products",
            "What would you recommend for someone new to skincare?",
            "Sounds good, let me think about it"
        ]
    )

if __name__ == "__main__":
    run_comprehensive_tests()
    print("\n🎉 All test scenarios completed!")
    print("Review the responses above to evaluate the agent's performance.")
