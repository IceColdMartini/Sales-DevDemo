"""
Conversation Backbone
====================

Main integration point for the advanced conversation system.
This is the primary conversation handler that coordinates all new conversation modules.
Replaces all legacy conversation services with a unified, modern architecture.
"""

import logging
from typing import Dict, List, Any, Optional
import asyncio
from datetime import datetime

from app.services.new_conversation.orchestrator import ConversationOrchestrator
from app.services.new_conversation.product_matcher import ProductMatcher
from app.services.new_conversation.response_generator import ResponseGenerator
from app.services.new_conversation.sales_analyzer import SalesFunnelAnalyzer
from app.services.new_conversation.state_manager import ConversationStateManager
from app.services.new_conversation import ConversationState, ConversationResponse

from app.db.postgres_handler import postgres_handler
from app.db.mongo_handler import mongo_handler
from app.core.config import settings

logger = logging.getLogger(__name__)

class ConversationBackbone:
    """
    Main conversation backbone that integrates all new conversation modules.
    This is the primary conversation handler for the entire application.

    Features:
    - Advanced LangChain-powered conversation processing
    - Sophisticated product matching with semantic similarity
    - Intelligent sales funnel analysis
    - Persistent conversation state management
    - Error-resilient processing with comprehensive logging
    - Unified API for all conversation operations
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Initialize core conversation orchestrator
        self.orchestrator = ConversationOrchestrator()

        # Direct access to individual components for advanced operations
        self.product_matcher = ProductMatcher()
        self.response_generator = ResponseGenerator()
        self.sales_analyzer = SalesFunnelAnalyzer()
        self.state_manager = ConversationStateManager()

        # Database connections
        self.postgres = postgres_handler
        self.mongo = mongo_handler

        self.logger.info("✅ Conversation Backbone initialized with all new modules")

    async def process_message(self, sender_id: str, user_message: str) -> Dict[str, Any]:
        """
        Main message processing method - primary entry point for all conversations.

        Args:
            sender_id: Unique identifier for the conversation
            user_message: The user's message text

        Returns:
            Dict containing standardized response with all conversation data
        """
        try:
            self.logger.info(f"🚀 Processing message from {sender_id}: {user_message[:50]}...")

            # Validate input
            if not user_message or not user_message.strip():
                return self._create_error_response(sender_id, "Empty message received")

            if len(user_message) > 2000:
                return self._create_error_response(sender_id, "Message too long (max 2000 characters)")

            # Process through the new conversation orchestrator
            response = await self.orchestrator.process_message(sender_id, user_message)

            # Convert to standardized API response format
            api_response = {
                "sender": response.sender,
                "product_interested": response.product_interested,
                "interested_product_ids": response.interested_product_ids,
                "response_text": response.response_text,
                "is_ready": response.is_ready,
                "conversation_stage": response.sales_stage,
                "confidence": response.confidence,
                "handover": response.handover,
                "new_system": True,
                "processing_timestamp": datetime.utcnow().isoformat(),
                "metadata": response.metadata or {}
            }

            self.logger.info(f"✅ Message processed successfully for {sender_id}")
            return api_response

        except Exception as e:
            self.logger.error(f"❌ Error processing message from {sender_id}: {e}")
            return await self._handle_processing_error(sender_id, user_message, str(e))

    async def get_conversation_status(self, sender_id: str) -> Dict[str, Any]:
        """
        Get comprehensive conversation status and analytics.

        Args:
            sender_id: Unique identifier for the conversation

        Returns:
            Dict with conversation statistics and current state
        """
        try:
            # Get conversation state from state manager
            state = await self.state_manager.get_conversation_state(sender_id)

            # Get conversation history from MongoDB
            mongo_data = self.mongo.get_conversation(sender_id)

            # Get sales analysis insights
            insights = await self.get_conversation_insights(sender_id)

            return {
                "sender_id": sender_id,
                "conversation_state": state.__dict__ if state else None,
                "message_count": len(mongo_data.get('conversation', [])) if mongo_data else 0,
                "last_interaction": mongo_data.get('updated_at') if mongo_data else None,
                "insights": insights,
                "system": "new_conversation_backbone"
            }

        except Exception as e:
            self.logger.error(f"❌ Error getting conversation status for {sender_id}: {e}")
            return {
                "sender_id": sender_id,
                "error": str(e),
                "system": "new_conversation_backbone"
            }

    async def clear_conversation(self, sender_id: str) -> bool:
        """
        Clear all conversation data for a sender.

        Args:
            sender_id: Unique identifier for the conversation

        Returns:
            bool: Success status
        """
        try:
            # Clear state from state manager
            state_cleared = await self.state_manager.clear_conversation(sender_id)

            # Clear from MongoDB
            mongo_cleared = self.mongo.delete_conversation(sender_id)

            success = state_cleared and mongo_cleared
            if success:
                self.logger.info(f"✅ Conversation cleared for {sender_id}")
            else:
                self.logger.warning(f"⚠️ Partial conversation clear for {sender_id}")

            return success

        except Exception as e:
            self.logger.error(f"❌ Error clearing conversation for {sender_id}: {e}")
            return False

    async def get_conversation_insights(self, sender_id: str) -> Dict[str, Any]:
        """
        Get advanced insights about the conversation using all new modules.

        Args:
            sender_id: Unique identifier for the conversation

        Returns:
            Dict with comprehensive conversation insights
        """
        try:
            # Get current state
            state = await self.state_manager.get_conversation_state(sender_id)

            if not state:
                return {
                    "conversation_length": 0,
                    "current_stage": "NO_CONVERSATION",
                    "products_discussed": 0,
                    "insights_available": False
                }

            # Get conversation history
            mongo_data = self.mongo.get_conversation(sender_id)
            conversation_history = mongo_data.get('conversation', []) if mongo_data else []

            # Analyze with sales analyzer
            sales_insights = await self.sales_analyzer.analyze_conversation(
                conversation_history, [], state.current_stage, ""  # Use current state and empty message
            )

            return {
                "conversation_length": len(conversation_history),
                "current_stage": state.current_stage,
                "products_discussed": len(state.interested_products),
                "product_ids": state.product_ids,
                "sales_insights": sales_insights.__dict__ if sales_insights else None,
                "insights_available": True,
                "last_updated": state.last_updated.isoformat() if hasattr(state, 'last_updated') else None
            }

        except Exception as e:
            self.logger.error(f"❌ Error getting insights for {sender_id}: {e}")
            return {
                "conversation_length": 0,
                "current_stage": "ERROR",
                "products_discussed": 0,
                "insights_available": False,
                "error": str(e)
            }

    async def get_product_recommendations(self, sender_id: str, query: str = None) -> List[Dict]:
        """
        Get personalized product recommendations using the new product matcher.

        Args:
            sender_id: Unique identifier for the conversation
            query: Optional search query

        Returns:
            List of recommended products with scores
        """
        try:
            # Get user's conversation context
            state = await self.state_manager.get_conversation_state(sender_id)

            # Get all products from database
            all_products = self.postgres.get_all_products()

            if not all_products:
                return []

            # Use product matcher for recommendations
            if query:
                # Search-based recommendations
                matches = await self.product_matcher.find_matching_products(query, all_products)
            else:
                # Context-based recommendations from conversation state
                user_interests = []
                if state and state.interested_products:
                    user_interests = [p.get('name', '') for p in state.interested_products]

                if user_interests:
                    # Find similar products to user's interests
                    matches = await self.product_matcher.find_matching_products(
                        ' '.join(user_interests), all_products
                    )
                else:
                    # Return popular/high-rated products
                    matches = await self.product_matcher.find_matching_products(
                        "popular products", all_products
                    )

            # Convert to API format
            recommendations = []
            for match in matches[:10]:  # Top 10 recommendations
                recommendations.append({
                    "product": match.product.__dict__ if hasattr(match, 'product') else match,
                    "score": match.confidence if hasattr(match, 'confidence') else 0.5,
                    "match_type": "semantic" if query else "contextual"
                })

            return recommendations

        except Exception as e:
            self.logger.error(f"❌ Error getting recommendations for {sender_id}: {e}")
            return []

    def _create_error_response(self, sender_id: str, error_message: str) -> Dict[str, Any]:
        """Create a standardized error response."""
        return {
            "sender": sender_id,
            "response_text": f"I apologize, but I encountered an issue: {error_message}",
            "product_interested": None,
            "interested_product_ids": [],
            "is_ready": False,
            "conversation_stage": "ERROR",
            "confidence": 0.0,
            "new_system": True,
            "error": True,
            "error_message": error_message
        }

    async def _handle_processing_error(self, sender_id: str, user_message: str, error: str) -> Dict[str, Any]:
        """Handle processing errors with fallback response."""
        try:
            # Log the error with context
            self.logger.error(f"Processing failed for {sender_id}: {error}")

            # Attempt to save error context to conversation
            error_context = {
                "role": "system",
                "content": f"Error occurred during processing: {error}",
                "timestamp": datetime.utcnow().isoformat()
            }

            try:
                mongo_data = self.mongo.get_conversation(sender_id)
                conversation = mongo_data.get('conversation', []) if mongo_data else []
                conversation.append(error_context)
                self.mongo.save_conversation(sender_id, conversation)
            except Exception as save_error:
                self.logger.error(f"Failed to save error context: {save_error}")

            # Return user-friendly error response
            return {
                "sender": sender_id,
                "response_text": "I apologize, but I'm experiencing technical difficulties. Please try again in a moment.",
                "product_interested": None,
                "interested_product_ids": [],
                "is_ready": False,
                "conversation_stage": "ERROR",
                "confidence": 0.0,
                "new_system": True,
                "error": True,
                "error_details": error
            }

        except Exception as fallback_error:
            self.logger.critical(f"Critical error in error handler: {fallback_error}")
            # Ultimate fallback
            return {
                "sender": sender_id,
                "response_text": "Service temporarily unavailable. Please try again later.",
                "product_interested": None,
                "interested_product_ids": [],
                "is_ready": False,
                "conversation_stage": "CRITICAL_ERROR",
                "confidence": 0.0,
                "new_system": True,
                "error": True
            }

# Create the main conversation backbone instance
conversation_backbone = ConversationBackbone()
