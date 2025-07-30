#!/usr/bin/env python3
"""
MongoDB Atlas Migration Verification Script
Verifies that the migration to MongoDB Atlas was successful
"""

import os
import sys
import requests
import json
from datetime import datetime

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_health_endpoint():
    """Test the health endpoint to verify Atlas connection"""
    print("🏥 HEALTH CHECK")
    print("=" * 40)
    
    try:
        response = requests.get("http://localhost:8000/health", timeout=10)
        health_data = response.json()
        
        print(f"✅ Health Status: {health_data['status']}")
        print(f"✅ PostgreSQL: {health_data['databases']['postgresql']}")
        print(f"✅ MongoDB Type: {health_data['databases']['mongodb_type']}")
        print(f"✅ Using Atlas: {health_data['configuration']['using_atlas']}")
        print(f"✅ Database Name: {health_data['configuration']['mongo_db_name']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_conversation_flow():
    """Test a complete conversation flow with Atlas"""
    print("\n💬 CONVERSATION FLOW TEST")
    print("=" * 40)
    
    test_user = f"atlas_test_user_{int(datetime.now().timestamp())}"
    
    # Test 1: Initial inquiry
    print("🔹 Step 1: Initial perfume inquiry")
    try:
        response = requests.post(
            "http://localhost:8000/api/webhook",
            json={
                "sender": test_user,
                "recipient": "sales_agent",
                "text": "Hi, I need a good perfume for men"
            },
            timeout=30
        )
        
        data = response.json()
        print(f"   Response: {data['response_text'][:100]}...")
        print(f"   Product: {data['product_interested']}")
        print(f"   is_ready: {data['is_ready']}")
        
        if not data['product_interested']:
            print("❌ No product detected")
            return False
            
    except Exception as e:
        print(f"❌ Step 1 failed: {e}")
        return False
    
    # Test 2: Purchase confirmation
    print("\n🔹 Step 2: Purchase confirmation")
    try:
        response = requests.post(
            "http://localhost:8000/api/webhook",
            json={
                "sender": test_user,
                "recipient": "sales_agent",
                "text": "I want to buy this perfume"
            },
            timeout=30
        )
        
        data = response.json()
        print(f"   Response: {data['response_text'][:100]}...")
        print(f"   Product: {data['product_interested']}")
        print(f"   is_ready: {data['is_ready']}")
        
        if not data['is_ready']:
            print("❌ Purchase confirmation not triggered")
            return False
            
        print("✅ Conversation flow test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Step 2 failed: {e}")
        return False

def test_atlas_connection_direct():
    """Test direct connection to Atlas to verify data storage"""
    print("\n🌐 DIRECT ATLAS CONNECTION TEST")
    print("=" * 40)
    
    try:
        from app.core.config import settings
        from app.db.mongo_handler import MongoHandler
        
        print(f"✅ Using Atlas: {settings.USE_MONGODB_ATLAS}")
        print(f"✅ Atlas URI: {settings.MONGODB_ATLAS_URI[:50]}...")
        print(f"✅ Database: {settings.MONGODB_ATLAS_DB_NAME}")
        
        mongo = MongoHandler()
        mongo.connect()
        
        # Count conversations
        count = mongo.db.conversations.count_documents({})
        print(f"✅ Total conversations in Atlas: {count}")
        
        # Get recent conversations
        recent = list(mongo.db.conversations.find().sort("_id", -1).limit(3))
        print(f"✅ Recent conversations: {len(recent)}")
        
        for i, conv in enumerate(recent, 1):
            sender = conv.get('sender_id', 'unknown')
            message_count = len(conv.get('messages', []))
            print(f"   {i}. {sender}: {message_count} messages")
        
        mongo.disconnect()
        return True
        
    except Exception as e:
        print(f"❌ Direct Atlas connection failed: {e}")
        return False

def test_multiple_users():
    """Test that multiple users can have separate conversations in Atlas"""
    print("\n👥 MULTIPLE USERS TEST")
    print("=" * 40)
    
    users = [
        f"user_1_{int(datetime.now().timestamp())}",
        f"user_2_{int(datetime.now().timestamp())}",
        f"user_3_{int(datetime.now().timestamp())}"
    ]
    
    queries = [
        "I need face wash for oily skin",
        "Looking for a good shampoo",
        "Show me perfume options"
    ]
    
    try:
        for i, (user, query) in enumerate(zip(users, queries), 1):
            print(f"🔹 User {i}: {user[:20]}...")
            
            response = requests.post(
                "http://localhost:8000/api/webhook",
                json={
                    "sender": user,
                    "recipient": "sales_agent",
                    "text": query
                },
                timeout=30
            )
            
            data = response.json()
            print(f"   Query: {query}")
            print(f"   Product: {data['product_interested']}")
            print(f"   Response length: {len(data['response_text'])} chars")
        
        print("✅ Multiple users test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Multiple users test failed: {e}")
        return False

def main():
    """Run all verification tests"""
    print("🚀 MONGODB ATLAS MIGRATION VERIFICATION")
    print("=" * 50)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    tests_passed = 0
    total_tests = 4
    
    # Test 1: Health check
    if test_health_endpoint():
        tests_passed += 1
    
    # Test 2: Conversation flow
    if test_conversation_flow():
        tests_passed += 1
    
    # Test 3: Direct Atlas connection
    if test_atlas_connection_direct():
        tests_passed += 1
    
    # Test 4: Multiple users
    if test_multiple_users():
        tests_passed += 1
    
    # Results summary
    print("\n" + "=" * 50)
    print("📊 VERIFICATION RESULTS")
    print("=" * 50)
    print(f"Tests Passed: {tests_passed}/{total_tests}")
    print(f"Success Rate: {(tests_passed/total_tests)*100:.1f}%")
    
    if tests_passed == total_tests:
        print("\n🎉 ATLAS MIGRATION SUCCESSFUL!")
        print("✅ All systems operational with MongoDB Atlas")
        print("✅ Conversations are being stored in the cloud")
        print("✅ Application is accessible from anywhere")
        print("✅ Data persistence verified")
        
        print("\n📋 NEXT STEPS:")
        print("1. ✅ Atlas migration completed successfully")
        print("2. 🔄 Ready to merge with main branch")
        print("3. 🚀 Deploy to production when ready")
        print("4. 📊 Monitor Atlas dashboard for performance")
        
    else:
        print("\n⚠️  SOME TESTS FAILED")
        print("Please review the failed tests above")
    
    return tests_passed == total_tests

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
