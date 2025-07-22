#!/usr/bin/env python3
"""
Test script to demonstrate the enhanced conversation handling capabilities
"""

import asyncio
import json
from app.models.schemas import Message
from app.services.conversation_service import conversation_service

async def test_conversation_scenarios():
    """Test various conversation scenarios to demonstrate improvements"""
    
    test_scenarios = [
        {
            "name": "Product-related inquiry",
            "sender": "test_user_product",
            "messages": [
                "I'm looking for a good perfume",
                "Tell me what our current conversation is about"
            ]
        },
        {
            "name": "Off-topic conversation",
            "sender": "test_user_offtopic", 
            "messages": [
                "I'm looking for a good perfume",
                "The weather is really nice today",
                "Tell me what we were discussing"
            ]
        },
        {
            "name": "General chat",
            "sender": "test_user_chat",
            "messages": [
                "Hi there!",
                "How are you doing?",
                "What products do you have?"
            ]
        },
        {
            "name": "Mixed conversation",
            "sender": "test_user_mixed",
            "messages": [
                "I need a good shampoo for hair fall",
                "By the way, what's your favorite movie?",
                "Let's get back to hair care products"
            ]
        }
    ]
    
    print("🧪 Testing Enhanced Conversation System")
    print("=" * 60)
    
    for scenario in test_scenarios:
        print(f"\n📋 Scenario: {scenario['name']}")
        print("-" * 40)
        
        for i, message_text in enumerate(scenario['messages'], 1):
            print(f"\n👤 Customer Message {i}: \"{message_text}\"")
            
            # Create message object
            message = Message(
                sender=scenario['sender'],
                recipient="test_page",
                text=message_text
            )
            
            try:
                # Process the message
                response = await conversation_service.process_message(message)
                
                print(f"🤖 AI Response: {response['response_text']}")
                print(f"🎯 Product Interest: {response['product_interested']}")
                print(f"🚀 Ready to Buy: {response['is_ready']}")
                
            except Exception as e:
                print(f"❌ Error: {str(e)}")
            
            print()
    
    print("\n✅ Testing completed!")
    print("\nKey improvements demonstrated:")
    print("1. Context-aware responses to off-topic conversations")
    print("2. Natural transitions back to product discussions")
    print("3. Conversation summary capabilities")
    print("4. Human-like acknowledgment of user inputs")
    print("5. Intelligent keyword extraction (empty for off-topic)")

if __name__ == "__main__":
    asyncio.run(test_conversation_scenarios())
