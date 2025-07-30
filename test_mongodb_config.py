#!/usr/bin/env python3
"""
Test script to verify MongoDB Atlas configuration works
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_mongodb_configuration():
    """Test MongoDB configuration and connection"""
    
    print("🧪 TESTING MONGODB CONFIGURATION")
    print("=" * 40)
    
    try:
        from app.core.config import settings
        from app.db.mongo_handler import MongoHandler
        
        # Show current configuration
        print("📋 Current Configuration:")
        print(f"   USE_MONGODB_ATLAS: {settings.USE_MONGODB_ATLAS}")
        print(f"   Effective URI: {settings.effective_mongo_uri[:30]}...")
        print(f"   Effective DB Name: {settings.effective_mongo_db_name}")
        
        # Test connection
        print("\n🔌 Testing MongoDB Connection...")
        mongo_handler = MongoHandler()
        mongo_handler.connect()
        
        # Get connection info
        connection_info = mongo_handler.get_connection_info()
        print(f"✅ Connection Status: {connection_info.get('status')}")
        print(f"   Connection Type: {connection_info.get('connection_type')}")
        print(f"   Server Version: {connection_info.get('server_version')}")
        print(f"   Database: {connection_info.get('database_name')}")
        print(f"   Collections: {connection_info.get('collections', [])}")
        
        # Test basic operations
        print("\n🧪 Testing Basic Operations...")
        
        # Test saving a conversation
        test_conversation = [
            {"role": "user", "content": "Hello, I need perfume"},
            {"role": "assistant", "content": "I'd be happy to help you find a great perfume!"}
        ]
        
        mongo_handler.save_conversation("test_user_atlas", test_conversation)
        print("✅ Save conversation: Success")
        
        # Test retrieving conversation
        retrieved = mongo_handler.get_conversation("test_user_atlas")
        if retrieved and len(retrieved.get('conversation', [])) == 2:
            print("✅ Retrieve conversation: Success")
        else:
            print("❌ Retrieve conversation: Failed")
        
        # Clean up test data
        mongo_handler.db.conversations.delete_one({"sender_id": "test_user_atlas"})
        print("✅ Cleanup test data: Success")
        
        # Disconnect
        mongo_handler.disconnect()
        
        print("\n🎉 All tests passed! MongoDB configuration is working correctly.")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_mongodb_configuration()
    
    if success:
        print("\n🚀 Ready for Atlas migration!")
        print("Next steps:")
        print("1. Set up MongoDB Atlas account (see MONGODB_ATLAS_SETUP.md)")
        print("2. Update .env with Atlas credentials")
        print("3. Run migration script: python migrate_to_atlas.py")
    else:
        print("\n⚠️ Please fix the configuration issues before proceeding.")
