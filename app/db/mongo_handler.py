
from pymongo import MongoClient
from app.core.config import settings
from typing import List, Dict, Optional
from datetime import datetime

class MongoHandler:
    def __init__(self):
        self.client = None
        self.db = None

    def connect(self):
        try:
            self.client = MongoClient(settings.MONGO_URI)
            self.db = self.client[settings.MONGO_DB_NAME]
            print("MongoDB connection established.")
        except Exception as e:
            print(f"Error connecting to MongoDB: {e}")
            raise

    def disconnect(self):
        if self.client:
            self.client.close()
        print("MongoDB connection closed.")

    def get_conversation(self, sender_id: str) -> Optional[Dict]:
        """Get conversation history for a specific sender"""
        try:
            return self.db.conversations.find_one({"sender_id": sender_id})
        except Exception as e:
            print(f"Error getting conversation for {sender_id}: {e}")
            return None

    def save_conversation(self, sender_id: str, conversation: List[Dict]):
        """Save or update conversation history for a sender"""
        try:
            self.db.conversations.update_one(
                {"sender_id": sender_id},
                {
                    "$set": {
                        "conversation": conversation,
                        "updated_at": datetime.utcnow(),
                        "message_count": len(conversation)
                    },
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
            result = self.db.conversations.delete_one({"sender_id": sender_id})
            return result.deleted_count > 0
        except Exception as e:
            print(f"Error deleting conversation for {sender_id}: {e}")
            return False

    def get_all_active_conversations(self) -> List[Dict]:
        """Get list of all active conversations"""
        try:
            return list(self.db.conversations.find(
                {},
                {"sender_id": 1, "message_count": 1, "updated_at": 1}
            ).sort("updated_at", -1))
        except Exception as e:
            print(f"Error getting active conversations: {e}")
            return []

mongo_handler = MongoHandler()
