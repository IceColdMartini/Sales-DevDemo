#!/usr/bin/env python3
"""
Test script to verify product matching and LLM reasoning functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import asyncio
from app.services.ai_service import AIService
from app.services.conversation_service import ConversationService
from app.db.postgres_handler import postgres_handler
from app.db.mongo_handler import mongo_handler
from app.models.schemas import Message

def mock_conversation_methods():
    """Mock MongoDB conversation methods for testing when MongoDB is not available"""
    original_get_conversation = mongo_handler.get_conversation
    original_save_conversation = mongo_handler.save_conversation
    
    def mock_get_conversation(sender_id):
        print(f"   🔍 Mock: Getting conversation for {sender_id} (returning empty)")
        return None
    
    def mock_save_conversation(sender_id, conversation):
        print(f"   💾 Mock: Saving conversation for {sender_id} ({len(conversation)} messages)")
        return True
    
    mongo_handler.get_conversation = mock_get_conversation
    mongo_handler.save_conversation = mock_save_conversation
    
    return original_get_conversation, original_save_conversation

async def test_product_matching():
    """Test the complete product matching workflow"""
    
    print("🧪 TESTING PRODUCT MATCHING AND LLM REASONING")
    print("=" * 60)
    
    # Initialize services
    ai_service = AIService()
    conversation_service = ConversationService()
    
    # Connect to databases
    print("🔌 Connecting to databases...")
    postgres_handler.connect()
    
    # Try to connect to MongoDB (optional for testing)
    mongodb_available = False
    original_methods = None
    try:
        mongo_handler.connect()
        mongodb_available = True
        print("✅ MongoDB connected successfully")
    except Exception as e:
        print(f"⚠️ MongoDB connection failed: {e}")
        print("📝 Using mock conversation methods for testing")
        mongodb_available = False
        original_methods = mock_conversation_methods()
    
    # Test messages
    test_messages = [
        "I need a good perfume for special occasions",
        "Looking for anti-dandruff shampoo", 
        "I want something for hair fall control",
        "Need a face wash for acne prone skin",
        "Show me some moisturizing soap",
        "I'll take the Wild Stone perfume",  # Purchase intent
        "What perfumes do you have under 300?"  # Price constraint
    ]
    
    for i, message_text in enumerate(test_messages, 1):
        print(f"\n🔍 TEST {i}: {message_text}")
        print("-" * 50)
        
        # 1. Test keyword extraction
        print("1️⃣ KEYWORD EXTRACTION:")
        keywords = await ai_service.extract_keywords_with_llm(message_text)
        print(f"   Keywords: {keywords}")
        
        # 2. Test product search
        print("\n2️⃣ PRODUCT SEARCH:")
        all_products = postgres_handler.get_all_products()
        matching_products = ai_service.find_matching_products_with_llm(keywords, all_products)
        
        print(f"   Found {len(matching_products)} matching products:")
        for product, score in matching_products:
            print(f"   • {product['name']} (Score: {score:.1f}%, ID: {product['id']})")
        
        # 3. Test conversation processing
        print("\n3️⃣ CONVERSATION PROCESSING:")
        message = Message(
            sender="test_user_123",
            recipient="test_page",
            text=message_text
        )
        
        try:
            response = await conversation_service.process_message(message)
            print(f"   Product Interested: {response['product_interested']}")
            print(f"   Product IDs: {response['interested_product_ids']}")
            print(f"   Is Ready: {response['is_ready']}")
            print(f"   Response: {response['response_text'][:100]}...")
        except Exception as e:
            print(f"   ❌ Error: {e}")
            if "conversations" in str(e):
                print("   ℹ️  This error is related to conversation storage (should be handled by mock)")
        
        print("\n" + "="*60)
    
    # Disconnect from databases
    postgres_handler.disconnect()
    if mongodb_available:
        mongo_handler.disconnect()
    elif original_methods:
        # Restore original methods
        mongo_handler.get_conversation, mongo_handler.save_conversation = original_methods
    
    print("\n✅ Product matching tests completed!")

async def test_tag_matching():
    """Test tag-based product matching specifically"""
    
    print("\n🏷️ TESTING TAG-BASED MATCHING")
    print("=" * 60)
    
    ai_service = AIService()
    postgres_handler.connect()
    
    # Get all products
    all_products = postgres_handler.get_all_products()
    
    # Test different keyword combinations
    test_cases = [
        ["perfume", "masculine", "woody"],
        ["anti-dandruff", "shampoo"],
        ["hair", "fall", "control"],
        ["face", "wash", "neem"],
        ["moisturizing", "soap"],
        ["antibacterial", "protection"]
    ]
    
    for keywords in test_cases:
        print(f"\n🔍 Testing keywords: {keywords}")
        
        # Test postgres tag search
        postgres_matches = postgres_handler.get_products_by_tags(keywords)
        print(f"   PostgreSQL tag search: {len(postgres_matches)} products")
        
        # Test LLM-based matching
        llm_matches = ai_service.find_matching_products_with_llm(keywords, all_products)
        print(f"   LLM-based matching: {len(llm_matches)} products")
        
        # Show top matches
        for product, score in llm_matches[:3]:
            tags = product.get('product_tag', [])
            matching_tags = [tag for tag in tags if any(kw.lower() in tag.lower() for kw in keywords)]
            print(f"   • {product['name']} (Score: {score:.1f}%)")
            print(f"     Matching tags: {matching_tags}")
    
    postgres_handler.disconnect()
    print("\n✅ Tag matching tests completed!")

if __name__ == "__main__":
    print("🚀 Starting Product Database and Matching Tests\n")
    
    # Run tests
    asyncio.run(test_product_matching())
    asyncio.run(test_tag_matching())
    
    print("\n🎉 All tests completed!")
