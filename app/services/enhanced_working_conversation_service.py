"""
Enhanced Working Conversation Service
====================================

This service integrates the working LangChain conversation service
with the existing conversation workflow.
"""

import logging
from typing import Dict, Any, List
import json
import asyncio

logger = logging.getLogger(__name__)

class EnhancedWorkingConversationService:
    """Enhanced conversation service using the working LangChain integration"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Initialize services
        self.langchain_service = None
        self.ai_service = None
        self.conversation_service = None
        
        self._initialize_services()

    def _initialize_services(self):
        """Initialize all required services with fallback handling"""
        try:
            # Import existing AI service
            from app.services.ai_service import ai_service
            self.ai_service = ai_service
            self.logger.info("✅ AI service connected")
        except ImportError as e:
            self.logger.error(f"❌ Failed to import AI service: {e}")

        try:
            # Import existing conversation service
            from app.services.conversation_service import conversation_service
            self.conversation_service = conversation_service
            self.logger.info("✅ Conversation service connected")
        except ImportError as e:
            self.logger.error(f"❌ Failed to import conversation service: {e}")

        self.logger.info("✅ Enhanced working conversation service initialized")

    async def process_enhanced_conversation(self, sender_id: str, user_message: str, 
                                          conversation_history: str = "") -> Dict[str, Any]:
        """
        Process conversation using enhanced LangChain-powered approach
        
        Returns:
            Dict containing response, products, stage analysis, and metadata
        """
        try:
            # Step 0: Validate and sanitize input
            if not user_message or not user_message.strip():
                return {
                    "sender": sender_id,
                    "response_text": "I didn't receive your message clearly. Could you please try again?",
                    "response": "I didn't receive your message clearly. Could you please try again?",  # For test compatibility
                    "is_ready": False,
                    "products": [],
                    "keywords": [],
                    "sales_stage": "INITIAL_INTEREST",
                    "confidence": 0.5,
                    "enhanced": True,
                    "langchain_powered": False
                }
            
            # Handle extremely long messages
            MAX_MESSAGE_LENGTH = 2000
            if len(user_message) > MAX_MESSAGE_LENGTH:
                self.logger.warning(f"⚠️ Long message detected ({len(user_message)} chars), truncating")
                user_message = user_message[:MAX_MESSAGE_LENGTH] + "..."
            
            # Step 1: Get existing conversation state
            conversation_state = self.get_conversation_memory(sender_id)
            previous_products = conversation_state.get("products", [])
            previous_stage = conversation_state.get("stage", "INITIAL_INTEREST")
            
            # Get conversation history from memory
            memory = conversation_state.get("memory")
            chat_history = ""
            if memory and hasattr(memory, 'chat_memory'):
                try:
                    messages = memory.chat_memory.messages
                    # Convert messages to string format for analysis
                    history_parts = []
                    for msg in messages[-10:]:  # Last 10 messages for context
                        if hasattr(msg, 'type'):
                            if msg.type == 'human':
                                history_parts.append(f"Customer: {msg.content}")
                            elif msg.type == 'ai':
                                history_parts.append(f"Assistant: {msg.content}")
                    chat_history = "\n".join(history_parts)
                except Exception as e:
                    self.logger.error(f"❌ Failed to retrieve chat history: {e}")
                    chat_history = conversation_history
            
            self.logger.info(f"📚 Retrieved conversation state: {len(previous_products)} products, stage: {previous_stage}")
            
            # Step 2: Extract keywords using LangChain
            keyword_extraction = None
            if self.langchain_service:
                keyword_extraction = self.langchain_service.extract_keywords_with_langchain(user_message)
                self.logger.info(f"📝 Keywords extracted: {keyword_extraction.keywords}")
            
            # Step 3: Get products from database
            products = []
            try:
                from app.db.postgres_handler import postgres_handler
                products = postgres_handler.get_all_products()
                self.logger.info(f"🛍️ Retrieved {len(products)} products from database")
            except Exception as e:
                self.logger.error(f"❌ Failed to get products: {e}")
                products = []

            # Step 4: Find matching products (combine with previous products)
            matching_products = []
            if self.langchain_service and keyword_extraction and products:
                try:
                    matches = await self.langchain_service.find_matching_products_with_langchain(
                        keyword_extraction.keywords, products
                    )
                    matching_products = [match[0] for match in matches[:5]]  # Top 5 products
                    
                    # Include previously discussed products if relevant
                    for prev_product in previous_products:
                        if prev_product not in matching_products:
                            matching_products.append(prev_product)
                    
                    self.logger.info(f"🎯 Found {len(matching_products)} matching products (including {len(previous_products)} previous)")
                except Exception as e:
                    self.logger.error(f"❌ Product matching failed: {e}")
                    matching_products = previous_products  # Fallback to previous products

            # Step 5: Analyze sales stage with conversation context
            sales_analysis = None
            if self.langchain_service:
                try:
                    # Prepare product info for analysis
                    product_info = self._format_product_info(matching_products)
                    
                    # Use conversation history for better analysis
                    full_history = chat_history if chat_history else conversation_history
                    
                    sales_analysis = await self.langchain_service.analyze_sales_stage_with_langchain(
                        full_history, user_message, product_info
                    )
                    self.logger.info(f"📊 Sales stage: {sales_analysis.current_stage} (previous: {previous_stage})")
                except Exception as e:
                    self.logger.error(f"❌ Sales analysis failed: {e}")

            # Step 6: Generate response with conversation context
            response_data = None
            if self.langchain_service and sales_analysis:
                try:
                    product_info = self._format_product_info(matching_products)
                    
                    response_data = await self.langchain_service.generate_response_with_langchain(
                        chat_history, user_message, sales_analysis, product_info, sender_id
                    )
                    self.logger.info("💬 Response generated successfully")
                except Exception as e:
                    self.logger.error(f"❌ Response generation failed: {e}")

            # Step 7: Update conversation state
            if self.langchain_service and matching_products and sales_analysis:
                try:
                    self.langchain_service.update_conversation_state(
                        sender_id, matching_products, sales_analysis.current_stage
                    )
                    self.logger.info("🔄 Conversation state updated")
                except Exception as e:
                    self.logger.error(f"❌ State update failed: {e}")

            # Step 8: Save conversation to MongoDB
            if self.conversation_service and response_data:
                try:
                    # Create a Message object and save the conversation
                    from app.models.schemas import Message
                    message_obj = Message(sender=sender_id, recipient="assistant", text=user_message)
                    await self.conversation_service.process_message(message_obj)
                    self.logger.info("💾 Conversation saved to MongoDB")
                except Exception as e:
                    self.logger.error(f"❌ Failed to save conversation: {e}")

            # Step 9: Prepare final response
            if response_data and sales_analysis:
                # Extract product IDs from matching products
                interested_product_ids = [p.get('id') for p in matching_products if p.get('id')]
                
                # Determine product interested (similar to basic service logic)
                product_interested = ""
                if sales_analysis.is_ready_to_buy and matching_products:
                    if len(matching_products) == 1:
                        product_interested = matching_products[0].get('name', '')
                    else:
                        names = [p.get('name', '') for p in matching_products]
                        product_interested = f"Multiple products: {', '.join(names)}"
                elif sales_analysis.interested_products:
                    product_interested = sales_analysis.interested_products[0] if sales_analysis.interested_products else ""
                elif matching_products:
                    product_interested = matching_products[0].get('name', '') if matching_products else ""
                
                return {
                    "sender": sender_id,
                    "product_interested": product_interested,
                    "interested_product_ids": interested_product_ids,
                    "response_text": response_data.response_text,
                    "response": response_data.response_text,  # For test compatibility
                    "is_ready": sales_analysis.is_ready_to_buy,
                    "is_ready_to_buy": sales_analysis.is_ready_to_buy,  # For test compatibility
                    "products": matching_products,
                    "keywords": keyword_extraction.keywords if keyword_extraction else [],
                    "sales_stage": sales_analysis.current_stage,
                    "confidence": sales_analysis.confidence_level,
                    "next_action": sales_analysis.next_action,
                    "urgency_level": response_data.urgency_level,
                    "enhanced": True,
                    "langchain_powered": True,
                    "conversation_context_used": True
                }
            else:
                # Fallback to basic conversation service
                return await self._fallback_conversation(sender_id, user_message)

        except Exception as e:
            self.logger.error(f"❌ Enhanced conversation processing failed: {e}")
            return await self._fallback_conversation(sender_id, user_message)

    def _format_product_info(self, products: List[Dict]) -> str:
        """Format product information for LLM consumption"""
        if not products:
            return "No specific products found."
        
        product_lines = []
        for i, product in enumerate(products[:5], 1):
            name = product.get('name', 'Unknown')
            price = product.get('price', 'Price not available')
            brand = product.get('brand', 'Brand not specified')
            
            product_lines.append(f"{i}. {name} by {brand} - {price}")
        
        return "\n".join(product_lines)

    async def _fallback_conversation(self, sender_id: str, user_message: str) -> Dict[str, Any]:
        """Fallback to basic conversation service if enhanced processing fails"""
        try:
            if self.conversation_service:
                self.logger.info("🔄 Using fallback conversation service")
                
                # Use existing conversation service
                from app.models.schemas import Message
                message_obj = Message(sender=sender_id, recipient="assistant", text=user_message)
                result = await self.conversation_service.process_message(message_obj)
                
                # Add enhanced flags
                result.update({
                    "enhanced": False,
                    "langchain_powered": False,
                    "fallback_used": True
                })
                
                # Ensure both response keys for test compatibility
                if "response" in result and "response_text" not in result:
                    result["response_text"] = result["response"]
                
                return result
            else:
                # Ultimate fallback
                response_text = "Thank you for your message! I'd be happy to help you find the perfect beauty and personal care products. How can I assist you today?"
                return {
                    "response": response_text,
                    "response_text": response_text,  # For test compatibility
                    "products": [],
                    "keywords": [],
                    "sales_stage": "INITIAL_INTEREST",
                    "is_ready_to_buy": False,
                    "confidence": 0.5,
                    "enhanced": False,
                    "langchain_powered": False,
                    "fallback_used": True,
                    "error": "Services unavailable"
                }
        except Exception as e:
            self.logger.error(f"❌ Fallback conversation failed: {e}")
            return {
                "response": "I apologize, but I'm experiencing technical difficulties. Please try again in a moment.",
                "products": [],
                "keywords": [],
                "sales_stage": "ERROR",
                "enhanced": False,
                "langchain_powered": False,
                "error": str(e)
            }

    def get_conversation_memory(self, sender_id: str) -> Dict:
        """Get conversation memory for a user"""
        if self.langchain_service:
            try:
                return self.langchain_service.get_conversation_state(sender_id)
            except Exception as e:
                self.logger.error(f"❌ Failed to get conversation memory: {e}")
        
        return {"memory": None, "products": [], "stage": "INITIAL_INTEREST"}

    def clear_conversation_memory(self, sender_id: str) -> bool:
        """Clear conversation memory for a user"""
        if self.langchain_service:
            try:
                # Reset the user's conversation state
                if sender_id in self.langchain_service.conversation_states:
                    del self.langchain_service.conversation_states[sender_id]
                self.logger.info(f"🗑️ Cleared conversation memory for {sender_id}")
                return True
            except Exception as e:
                self.logger.error(f"❌ Failed to clear conversation memory: {e}")
        
        return False

    async def get_conversation_insights(self, sender_id: str) -> Dict[str, Any]:
        """Get insights about the current conversation state"""
        try:
            if self.langchain_service:
                state = self.langchain_service.get_conversation_state(sender_id)
                
                # Get memory contents
                memory = state.get("memory")
                chat_history = []
                if memory and hasattr(memory, 'chat_memory'):
                    try:
                        chat_history = memory.chat_memory.messages
                    except:
                        chat_history = []
                
                return {
                    "conversation_length": len(chat_history),
                    "current_stage": state.get("stage", "INITIAL_INTEREST"),
                    "products_discussed": len(state.get("products", [])),
                    "memory_available": memory is not None,
                    "langchain_active": True
                }
            else:
                return {
                    "conversation_length": 0,
                    "current_stage": "UNKNOWN",
                    "products_discussed": 0,
                    "memory_available": False,
                    "langchain_active": False
                }
        except Exception as e:
            self.logger.error(f"❌ Failed to get conversation insights: {e}")
            return {
                "conversation_length": 0,
                "current_stage": "ERROR",
                "products_discussed": 0,
                "memory_available": False,
                "langchain_active": False,
                "error": str(e)
            }

# Create the enhanced working service instance
enhanced_working_conversation_service = EnhancedWorkingConversationService()
