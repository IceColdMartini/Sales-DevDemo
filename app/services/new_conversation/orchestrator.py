"""
Conversation Orchestrator
========================

Main orchestrator for             # Step 7: Generate response
            response = await self.response_generator.generate_response(
                user_message, conversation_state.conversation_history, matched_products, sales_analysis, sender_id, should_handover
            )LangChain-based conversation system.
Coordinates all components and manages the conversation flow.
"""

import logging
from typing import Dict, List, Any, Optional
import asyncio
from datetime import datetime

from .enhanced_sales_analyzer import enhanced_sales_analyzer
from .enhanced_product_matcher import enhanced_product_matcher
from .enhanced_response_generator import enhanced_response_generator, ResponseContext
from .state_manager import conversation_state_manager
from . import ConversationState, ConversationResponse

logger = logging.getLogger(__name__)

class ConversationOrchestrator:
    """
    Main orchestrator for the advanced conversation system.
    Handles the complete conversation flow from message processing to response generation.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Initialize enhanced components
        self.product_matcher = enhanced_product_matcher
        self.response_generator = enhanced_response_generator
        self.sales_analyzer = enhanced_sales_analyzer
        self.state_manager = conversation_state_manager

        self.logger.info("✅ Conversation Orchestrator initialized")

    async def process_message(self, sender_id: str, user_message: str) -> ConversationResponse:
        """
        Process a user message and generate a response.

        Args:
            sender_id: Unique identifier for the conversation
            user_message: The user's message text

        Returns:
            ConversationResponse: Standardized response with all required fields
        """
        try:
            self.logger.info(f"🚀 Processing message from {sender_id}: {user_message[:50]}...")

            # Step 1: Get or create conversation state
            conversation_state = await self.state_manager.get_conversation_state(sender_id)

            # Step 2: Add user message to conversation history
            await self.state_manager.add_message_to_history(sender_id, "user", user_message)

            # Step 3: Get available products from database
            from app.db.postgres_handler import postgres_handler
            available_products = postgres_handler.get_all_products()

            # Step 4: Match products using enhanced matcher
            matched_products = await self.product_matcher.find_matching_products(
                user_message, conversation_state.conversation_history, available_products
            )

            # Step 5: Analyze sales stage and readiness
            sales_analysis = await self.sales_analyzer.analyze_conversation(
                conversation_state.conversation_history, matched_products, conversation_state.current_stage, user_message
            )

            # Step 6: Check if handover to human agent is needed
            conversation_length = len(conversation_state.conversation_history)
            should_handover = self.sales_analyzer.should_handover_to_agent(sales_analysis, conversation_length)

            self.logger.info(f"🔄 Handover check: Stage={sales_analysis.current_stage}, Ready={sales_analysis.is_ready_to_buy}, Length={conversation_length}, Handover={should_handover}")

            # Step 7: Update conversation state
            await self.state_manager.update_conversation_state(
                sender_id, sales_analysis, matched_products
            )

            # Step 8: Generate enhanced response
            response_context = ResponseContext(
                customer_message=user_message,
                sales_stage=sales_analysis.current_stage,
                is_ready_to_buy=sales_analysis.is_ready_to_buy,
                conversation_history=conversation_state.conversation_history,
                matched_products=matched_products,
                customer_sentiment=sales_analysis.customer_sentiment,
                conversation_length=conversation_length,
                previous_topics=getattr(conversation_state, 'topics_discussed', [])
            )
            
            response = await self.response_generator.generate_response(response_context)

            # Step 9: Add AI response to conversation history
            response_text = response.get("message", "I'm here to help!")
            await self.state_manager.add_message_to_history(sender_id, "assistant", response_text)

            # Step 10: Prepare final response with accumulated product IDs
            # Get updated conversation state to get all accumulated products
            updated_state = await self.state_manager.get_conversation_state(sender_id)
            all_product_ids = getattr(updated_state, 'product_ids', [])
            
            # Extract product info from matched products
            product_interested = None
            if matched_products:
                product_interested = matched_products[0].product.get('name')
            
            final_response = ConversationResponse(
                sender=sender_id,
                product_interested=product_interested,
                interested_product_ids=all_product_ids,  # Use accumulated product IDs
                response_text=response_text,
                is_ready=sales_analysis.is_ready_to_buy,
                sales_stage=sales_analysis.current_stage,
                confidence=sales_analysis.confidence_score,
                handover=should_handover
            )

            self.logger.info(f"✅ Response generated for {sender_id}: Stage={final_response.sales_stage}, Ready={final_response.is_ready}")
            return final_response

        except Exception as e:
            self.logger.error(f"❌ Error processing message from {sender_id}: {e}")
            # Return error response
            return ConversationResponse(
                sender=sender_id,
                product_interested=None,
                interested_product_ids=[],
                response_text="I'm sorry, I encountered an error processing your message. Please try again.",
                is_ready=False,
                sales_stage="ERROR",
                confidence=0.0
            )

    async def get_conversation_status(self, sender_id: str) -> Dict[str, Any]:
        """Get the current status of a conversation"""
        try:
            state = await self.state_manager.get_conversation_state(sender_id)
            return {
                "sender_id": sender_id,
                "current_stage": state.current_stage,
                "is_ready": state.is_ready_to_buy,
                "product_count": len(state.interested_products),
                "conversation_turns": len(state.conversation_history),
                "last_interaction": state.last_interaction.isoformat()
            }
        except Exception as e:
            self.logger.error(f"Error getting conversation status for {sender_id}: {e}")
            return {"error": str(e)}

    async def clear_conversation(self, sender_id: str) -> bool:
        """Clear conversation history for a sender"""
        try:
            await self.state_manager.clear_conversation_state(sender_id)
            self.logger.info(f"🗑️ Cleared conversation for {sender_id}")
            return True
        except Exception as e:
            self.logger.error(f"Error clearing conversation for {sender_id}: {e}")
            return False

# Global orchestrator instance
conversation_orchestrator = ConversationOrchestrator()
