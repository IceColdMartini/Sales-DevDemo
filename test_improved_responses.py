#!/usr/bin/env python3
"""
Focused testing for the improved conversation handling
Tests the specific issues mentioned by the user
"""
import requests
import json
import time

API_BASE_URL = "http://localhost:8000"
WEBHOOK_URL = f"{API_BASE_URL}/api/webhook"

def send_message(sender_id: str, message: str) -> dict:
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

def test_improved_responses():
    """Test the specific issues mentioned by the user"""
    print("🧪 Testing Improved AI Responses")
    print("=" * 60)
    
    # Test Case 1: Conversation Summary Issue
    print("\n📋 TEST 1: Conversation Summary Handling")
    print("-" * 40)
    
    sender_id = "test_summary"
    clear_conversation(sender_id)
    
    # Build up a conversation
    print("Building conversation context...")
    send_message(sender_id, "I want to buy a body perfume")
    time.sleep(1)
    
    # Ask for conversation summary
    print("\n👤 User: Tell me what our current conversation is about.")
    response = send_message(sender_id, "Tell me what our current conversation is about.")
    print(f"🤖 Agent: {response.get('response_text', 'No response')}")
    print(f"📊 Analysis: Should reference actual conversation, not generic product list")
    
    time.sleep(2)
    
    # Test Case 2: Off-topic Conversation Handling  
    print("\n🌤️  TEST 2: Off-topic Conversation (Weather)")
    print("-" * 40)
    
    sender_id = "test_weather"
    clear_conversation(sender_id)
    
    # Start with product discussion
    send_message(sender_id, "Hello, I want to buy a body perfume")
    time.sleep(1)
    
    # Go off-topic
    print("\n👤 User: What's the weather like today?")
    response = send_message(sender_id, "What's the weather like today?")
    print(f"🤖 Agent: {response.get('response_text', 'No response')}")
    print(f"📊 Analysis: Should acknowledge weather question, then redirect naturally")
    
    time.sleep(2)
    
    # Test Case 3: Personal Life Sharing
    print("\n💼 TEST 3: Personal Life Sharing (Work)")
    print("-" * 40)
    
    sender_id = "test_personal"
    clear_conversation(sender_id)
    
    print("\n👤 User: I had a great day at work today")
    response = send_message(sender_id, "I had a great day at work today")
    print(f"🤖 Agent: {response.get('response_text', 'No response')}")
    print(f"📊 Analysis: Should congratulate them, then naturally transition to products")
    
    time.sleep(2)
    
    # Test Case 4: Conversation Flow After Off-topic
    print("\n🔄 TEST 4: Return to Product Discussion")
    print("-" * 40)
    
    print("\n👤 User: Actually, let's get back to the perfume discussion")
    response = send_message(sender_id, "Actually, let's get back to the perfume discussion")
    print(f"🤖 Agent: {response.get('response_text', 'No response')}")
    print(f"📊 Analysis: Should smoothly return to product discussion with context")
    
    time.sleep(2)
    
    # Test Case 5: General Greeting with Context
    print("\n👋 TEST 5: Casual Greeting")
    print("-" * 40)
    
    sender_id = "test_greeting"
    clear_conversation(sender_id)
    
    print("\n👤 User: Hey there! How are you doing?")
    response = send_message(sender_id, "Hey there! How are you doing?")
    print(f"🤖 Agent: {response.get('response_text', 'No response')}")
    print(f"📊 Analysis: Should respond warmly to greeting, then guide to products")
    
    time.sleep(2)
    
    # Test Case 6: Building Conversation Context
    print("\n🏗️  TEST 6: Building Conversation Context")
    print("-" * 40)
    
    sender_id = "test_context"
    clear_conversation(sender_id)
    
    # Build context step by step
    print("\n👤 User 1: Hi, I'm looking for a good perfume")
    response1 = send_message(sender_id, "Hi, I'm looking for a good perfume")
    print(f"🤖 Agent 1: {response1.get('response_text', 'No response')[:100]}...")
    
    time.sleep(1)
    
    print("\n👤 User 2: I prefer something with a fresh scent")
    response2 = send_message(sender_id, "I prefer something with a fresh scent")
    print(f"🤖 Agent 2: {response2.get('response_text', 'No response')[:100]}...")
    
    time.sleep(1)
    
    print("\n👤 User 3: Can you remind me what we were discussing?")
    response3 = send_message(sender_id, "Can you remind me what we were discussing?")
    print(f"🤖 Agent 3: {response3.get('response_text', 'No response')}")
    print(f"📊 Analysis: Should reference perfume discussion and fresh scent preference")
    
    print("\n✅ Testing Complete!")
    print("\n📝 IMPROVEMENTS TO LOOK FOR:")
    print("1. More natural acknowledgment of off-topic comments")
    print("2. Specific conversation summaries instead of generic product lists")
    print("3. Better emotional intelligence in responses")
    print("4. Smooth transitions back to product discussions")
    print("5. Context retention across conversation turns")

if __name__ == "__main__":
    test_improved_responses()
