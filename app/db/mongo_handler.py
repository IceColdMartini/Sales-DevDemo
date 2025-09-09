
from pymongo import MongoClient
from app.core.config import settings
from typing import List, Dict, Optional
from datetime import datetime

class MongoHandler:
    def __init__(self):
        self.client = None
        self.db = None
        self.connection_type = None

    def connect(self):
        try:
            # Use the effective MongoDB URI from settings
            mongo_uri = settings.effective_mongo_uri
            db_name = settings.effective_mongo_db_name
            
            # Determine connection type for logging
            if settings.USE_MONGODB_ATLAS:
                self.connection_type = "MongoDB Atlas (Cloud)"
            else:
                self.connection_type = "MongoDB Local"
            
            print(f"Connecting to {self.connection_type}...")
            
            # MongoDB Atlas requires different connection parameters
            if settings.USE_MONGODB_ATLAS:
                # Atlas connections should use TLS and have specific timeout settings
                self.client = MongoClient(
                    mongo_uri,
                    tls=True,
                    tlsAllowInvalidCertificates=False,
                    serverSelectionTimeoutMS=5000,  # 5 second timeout
                    connectTimeoutMS=10000,  # 10 second timeout
                    maxPoolSize=50,  # Connection pool size
                    retryWrites=True
                )
            else:
                # Local MongoDB connection
                self.client = MongoClient(mongo_uri)
            
            # Test the connection
            self.client.admin.command('ping')
            
            self.db = self.client[db_name]
            print(f"✅ {self.connection_type} connection established successfully")
            print(f"   Database: {db_name}")
            
            # Create indexes for better performance (especially important for Atlas)
            self._create_indexes()
            
        except Exception as e:
            print(f"❌ Error connecting to {self.connection_type}: {e}")
            print(f"   URI pattern: {mongo_uri[:20]}..." if mongo_uri else "No URI provided")
            raise

    def _create_indexes(self):
        """Create database indexes for better performance"""
        try:
            # Index on sender_id for faster conversation lookups
            self.db.conversations.create_index("sender_id", unique=True)
            
            # Index on updated_at for queries by time
            self.db.conversations.create_index("updated_at")
            
            print("✅ Database indexes created/verified")
        except Exception as e:
            print(f"⚠️ Warning: Could not create indexes: {e}")

    def disconnect(self):
        if self.client:
            self.client.close()
        print(f"✅ {self.connection_type} connection closed.")

    def get_connection_info(self) -> dict:
        """Get information about the current MongoDB connection"""
        if not self.client:
            return {"status": "disconnected"}
        
        try:
            # Test connection
            self.client.admin.command('ping')
            
            server_info = self.client.server_info()
            
            return {
                "status": "connected",
                "connection_type": self.connection_type,
                "server_version": server_info.get("version", "unknown"),
                "database_name": settings.effective_mongo_db_name,
                "collections": self.db.list_collection_names() if self.db is not None else []
            }
        except Exception as e:
            return {
                "status": "error", 
                "error": str(e),
                "connection_type": self.connection_type
            }

    def get_database(self):
        """Get the MongoDB database instance"""
        if self.db is None:
            raise Exception("Database not connected. Call connect() first.")
        return self.db

    def get_conversation(self, sender_id: str) -> Optional[Dict]:
        """Get conversation history for a specific sender"""
        try:
            # Ensure connection is established
            if self.client is None or self.db is None:
                self.connect()
            return self.db.conversations.find_one({"sender_id": sender_id})
        except Exception as e:
            print(f"Error getting conversation for {sender_id}: {e}")
            return None

    def save_conversation(self, sender_id: str, conversation_data):
        """Save or update conversation data for a sender"""
        try:
            # Ensure connection is established
            if self.client is None or self.db is None:
                self.connect()
            
            # Handle both list and dict formats for backward compatibility
            if isinstance(conversation_data, list):
                # Legacy format: just the conversation messages
                update_data = {
                    "conversation": conversation_data,
                    "updated_at": datetime.utcnow(),
                    "message_count": len(conversation_data)
                }
            elif isinstance(conversation_data, dict):
                # New format: full conversation data structure
                update_data = conversation_data.copy()
                update_data["updated_at"] = datetime.utcnow()
                
                # Remove created_at from $set if it exists (should only be in $setOnInsert)
                if "created_at" in update_data:
                    del update_data["created_at"]
                
                # Ensure conversation field exists and count messages
                if "conversation" in update_data and isinstance(update_data["conversation"], list):
                    update_data["message_count"] = len(update_data["conversation"])
                else:
                    update_data["message_count"] = 0
            else:
                raise ValueError(f"Invalid conversation_data type: {type(conversation_data)}")
            
            self.db.conversations.update_one(
                {"sender_id": sender_id},
                {
                    "$set": update_data,
                    "$setOnInsert": {
                        "created_at": datetime.utcnow()
                    }
                },
                upsert=True
            )
        except Exception as e:
            print(f"Error saving conversation for {sender_id}: {e}")
            raise

    def get_conversation_stats(self, sender_id: str) -> Dict:
        """Get conversation statistics for a sender"""
        try:
            conversation = self.get_conversation(sender_id)
            if not conversation:
                return {"message_count": 0, "last_interaction": None}
            
            return {
                "message_count": len(conversation.get('conversation', [])),
                "last_interaction": conversation.get('updated_at'),
                "first_interaction": conversation.get('created_at')
            }
        except Exception as e:
            print(f"Error getting conversation stats for {sender_id}: {e}")
            return {"message_count": 0, "last_interaction": None}

    def delete_conversation(self, sender_id: str):
        """Delete conversation history for a sender"""
        try:
            # Ensure connection is established
            if self.client is None or self.db is None:
                self.connect()
            result = self.db.conversations.delete_one({"sender_id": sender_id})
            return result.deleted_count > 0
        except Exception as e:
            print(f"Error deleting conversation for {sender_id}: {e}")
            return False

    def get_all_active_conversations(self) -> List[Dict]:
        """Get list of all active conversations"""
        try:
            # Ensure connection is established
            if self.client is None or self.db is None:
                self.connect()
            return list(self.db.conversations.find(
                {},
                {"sender_id": 1, "message_count": 1, "updated_at": 1}
            ).sort("updated_at", -1))
        except Exception as e:
            print(f"Error getting active conversations: {e}")
            return []

mongo_handler = MongoHandler()
