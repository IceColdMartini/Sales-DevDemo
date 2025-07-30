#!/usr/bin/env python3
"""
MongoDB Migration Script: Local to Atlas
Migrates conversation data from local MongoDB to MongoDB Atlas
"""

import os
import sys
from typing import Dict, List
from pymongo import MongoClient
from datetime import datetime

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def migrate_conversations():
    """Migrate conversations from local MongoDB to Atlas"""
    
    print("🚀 MONGODB MIGRATION: LOCAL → ATLAS")
    print("=" * 50)
    
    # Local MongoDB connection details
    local_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
    local_db_name = os.getenv("MONGO_DB_NAME", "conversations_db")
    
    # Atlas MongoDB connection details
    atlas_uri = os.getenv("MONGODB_ATLAS_URI", "mongodb+srv://sales_admin:icee@conversation.4cibmsx.mongodb.net/sales_conversations?retryWrites=true&w=majority&appName=Conversation")
    atlas_db_name = os.getenv("MONGODB_ATLAS_DB_NAME", "sales_conversations")
    
    if not atlas_uri:
        print("❌ Error: MONGODB_ATLAS_URI not found in environment variables")
        print("Please set up your Atlas connection string in .env file")
        return False
    
    try:
        # Connect to local MongoDB
        print("🔌 Connecting to local MongoDB...")
        local_client = MongoClient(local_uri)
        local_db = local_client[local_db_name]
        
        # Test local connection
        local_client.admin.command('ping')
        print("✅ Local MongoDB connected")
        
        # Get conversation count from local
        local_conversations = list(local_db.conversations.find({}))
        print(f"📊 Found {len(local_conversations)} conversations in local database")
        
        if len(local_conversations) == 0:
            print("ℹ️  No conversations to migrate")
            local_client.close()
            return True
        
        # Connect to Atlas
        print("🌐 Connecting to MongoDB Atlas...")
        atlas_client = MongoClient(
            atlas_uri,
            tls=True,
            tlsAllowInvalidCertificates=False,
            serverSelectionTimeoutMS=10000,
            connectTimeoutMS=15000,
            retryWrites=True
        )
        
        # Test Atlas connection
        atlas_client.admin.command('ping')
        atlas_db = atlas_client[atlas_db_name]
        print("✅ MongoDB Atlas connected")
        
        # Create indexes in Atlas
        print("📝 Creating indexes in Atlas...")
        atlas_db.conversations.create_index("sender_id", unique=True)
        atlas_db.conversations.create_index("updated_at")
        print("✅ Indexes created")
        
        # Migrate conversations
        print("🔄 Starting migration...")
        migrated_count = 0
        error_count = 0
        
        for conversation in local_conversations:
            try:
                # Add migration metadata
                conversation['migrated_at'] = datetime.utcnow()
                conversation['migration_source'] = 'local_mongodb'
                
                # Insert or update in Atlas
                atlas_db.conversations.replace_one(
                    {"sender_id": conversation["sender_id"]},
                    conversation,
                    upsert=True
                )
                
                migrated_count += 1
                
                if migrated_count % 10 == 0:
                    print(f"   Migrated {migrated_count}/{len(local_conversations)} conversations...")
                    
            except Exception as e:
                print(f"❌ Error migrating conversation {conversation.get('sender_id', 'unknown')}: {e}")
                error_count += 1
        
        print(f"✅ Migration completed!")
        print(f"   Successfully migrated: {migrated_count}")
        print(f"   Errors encountered: {error_count}")
        
        # Verify migration
        atlas_count = atlas_db.conversations.count_documents({})
        print(f"🔍 Verification: {atlas_count} conversations in Atlas")
        
        # Close connections
        local_client.close()
        atlas_client.close()
        
        return error_count == 0
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

def verify_atlas_connection():
    """Verify that Atlas connection is working"""
    print("🔍 ATLAS CONNECTION TEST")
    print("=" * 30)
    
    atlas_uri = os.getenv("MONGODB_ATLAS_URI")
    atlas_db_name = os.getenv("MONGODB_ATLAS_DB_NAME", "sales_conversations")
    
    if not atlas_uri:
        print("❌ MONGODB_ATLAS_URI not configured")
        return False
    
    try:
        print("🌐 Testing Atlas connection...")
        client = MongoClient(
            atlas_uri,
            tls=True,
            serverSelectionTimeoutMS=10000,
            connectTimeoutMS=15000
        )
        
        # Test connection
        client.admin.command('ping')
        
        # Get database info
        db = client[atlas_db_name]
        collections = db.list_collection_names()
        conversation_count = db.conversations.count_documents({})
        
        print("✅ Atlas connection successful!")
        print(f"   Database: {atlas_db_name}")
        print(f"   Collections: {collections}")
        print(f"   Conversations: {conversation_count}")
        
        client.close()
        return True
        
    except Exception as e:
        print(f"❌ Atlas connection failed: {e}")
        return False

if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    print("Select an option:")
    print("1. Test Atlas connection")
    print("2. Migrate conversations from local to Atlas")
    print("3. Both (test then migrate)")
    
    choice = input("Enter choice (1/2/3): ").strip()
    
    if choice in ["1", "3"]:
        print("\n" + "="*60)
        if not verify_atlas_connection():
            print("\n❌ Atlas connection test failed. Please check your configuration.")
            if choice == "3":
                print("Skipping migration due to connection issues.")
                sys.exit(1)
        else:
            print("\n✅ Atlas connection test passed!")
    
    if choice in ["2", "3"]:
        print("\n" + "="*60)
        success = migrate_conversations()
        
        if success:
            print("\n🎉 Migration completed successfully!")
            print("\nNext steps:")
            print("1. Update your .env file to set USE_MONGODB_ATLAS=true")
            print("2. Restart your application")
            print("3. Test the application with Atlas")
        else:
            print("\n❌ Migration encountered errors. Please check the logs above.")
    
    if choice not in ["1", "2", "3"]:
        print("Invalid choice. Please run the script again.")
