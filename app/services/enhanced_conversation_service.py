"""
Enhanced Conversation Service with LangChain Integration
========================================================

This service integrates the LangChain-powered conversation system with the existing
conversation workflow, providing a seamless upgrade path while maintaining backward
compatibility and ensuring production-ready, error-free conversation handling.

Key Features:
- Seamless integration with existing conversation_service.py
- LangChain-powered conversation chains for enhanced memory and context
- Fallback mechanisms for error resilience
- Production-grade conversation state management
- Advanced sales funnel analysis with LangChain
- Comprehensive product recommendation system
"""

import asyncio
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime

# Import both services
from app.services.working_langchain_service import (
    langchain_conversation_service, 
    KeywordExtraction, 
    SalesStageAnalysis, 
    ConversationResponse
)
from app.services.ai_service import ai_service
from app.db.mongo_handler import mongo_handler
from app.db.postgres_handler import postgres_handler
from app.models.schemas import Message

class EnhancedConversationService:
    """
    Production-ready conversation service that leverages LangChain for superior
    conversation handling while maintaining compatibility with existing systems.
    
    This service provides:
    - LangChain-powered conversation chains with intelligent fallbacks
    - Enhanced memory management for conversation continuity
    - Advanced sales funnel analysis
    - Error-resilient conversation flows
    - Comprehensive product matching and recommendation
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.langchain_service = langchain_conversation_service
        self.fallback_service = ai_service  # Original AI service as fallback
        self.conversation_states = {}  # Enhanced conversation state tracking
        self.use_langchain = True  # Flag to enable/disable LangChain
        
    async def process_message(self, message: Message) -> Dict[str, Any]:
        """
        Process incoming message with enhanced LangChain conversation handling.
        
        This method provides a production-ready conversation flow with:
        - LangChain-powered conversation analysis
        - Intelligent fallback mechanisms
        - Comprehensive error handling
        - Advanced conversation state management
        """
        try:
            self.logger.info(f"🚀 Processing message from {message.sender}: {message.text}")
            
            # 1. Get conversation history with enhanced formatting
            conversation_data = mongo_handler.get_conversation(message.sender)
            full_conversation = conversation_data['conversation'] if conversation_data else []
            
            # Keep manageable conversation history (last 20 messages)
            conversation_history = full_conversation[-20:] if len(full_conversation) > 20 else full_conversation
            is_first_interaction = len(full_conversation) == 0
            
            # 2. Enhanced keyword extraction with LangChain
            keywords_result = await self._extract_keywords_enhanced(message.text)
            keywords = keywords_result.keywords if keywords_result else []
            
            # Skip product matching for non-beauty related conversations
            if not keywords_result or not keywords_result.is_beauty_related:
                self.logger.info("🔍 Non-beauty related conversation detected")
                return await self._handle_off_topic_conversation(message, conversation_history)
            
            self.logger.info(f"🔑 Enhanced Keywords: {keywords}")
            
            # 3. Get product catalog for matching
            all_products = postgres_handler.get_all_products()
            
            # 4. Enhanced sales stage analysis with LangChain
            conversation_history_str = self._format_conversation_history(conversation_history)
            initial_product_info = self._build_initial_product_info(all_products[:10])
            
            sales_analysis = await self._analyze_sales_stage_enhanced(
                conversation_history_str, message.text, initial_product_info
            )
            
            self.logger.info(f"📊 Enhanced Sales Analysis: Stage={sales_analysis.current_stage}, Ready={sales_analysis.is_ready_to_buy}")
            
            # 5. Enhanced product matching with LangChain
            relevant_products_with_scores = []
            if keywords:
                relevant_products_with_scores = await self._find_matching_products_enhanced(
                    keywords, all_products
                )
                
                for product, score in relevant_products_with_scores[:3]:
                    self.logger.info(f"🎯 Enhanced Match: {product['name']} (Score: {score:.1f}%)")
            
            # Extract products for further processing
            relevant_products = [product for product, score in relevant_products_with_scores]
            
            # 6. Enhanced conversation state management
            if relevant_products:
                self._update_enhanced_conversation_state(
                    message.sender, relevant_products, sales_analysis.current_stage
                )
            
            # 7. Apply price filtering if customer mentioned budget
            if sales_analysis.price_range_mentioned and relevant_products:
                relevant_products = self._apply_price_filtering(
                    relevant_products, sales_analysis.price_range_mentioned
                )
            
            # 8. Get comprehensive conversation state
            conversation_state = self._get_enhanced_conversation_state(message.sender)
            all_tracked_products = conversation_state['products']
            
            # Combine current products with tracked products
            combined_products = list(all_tracked_products)
            for product in relevant_products:
                if not any(p['id'] == product['id'] for p in combined_products):
                    combined_products.append(product)
            
            # 9. Build comprehensive product information
            product_info = self._build_enhanced_product_info(combined_products)
            
            # 10. Generate enhanced response with LangChain
            response_result = await self._generate_response_enhanced(
                conversation_history_str,
                message.text,
                sales_analysis,
                product_info,
                conversation_state,
                is_first_interaction
            )
            
            response_text = response_result.response_text
            
            # 11. Update conversation memory
            updated_conversation = full_conversation + [
                {"role": "user", "content": message.text},
                {"role": "assistant", "content": response_text}
            ]
            mongo_handler.save_conversation(message.sender, updated_conversation)
            
            # Update LangChain memory
            self.langchain_service.update_conversation_memory(
                message.sender, message.text, response_text
            )
            
            # 12. Determine final product interest and IDs
            product_interested = self._determine_product_interest_enhanced(
                message.sender, sales_analysis, sales_analysis.is_ready_to_buy
            )
            
            interested_product_ids = self._extract_product_ids_enhanced(message.sender)
            
            # 13. Return comprehensive response
            return {
                "sender": message.sender,
                "product_interested": product_interested,
                "interested_product_ids": interested_product_ids,
                "response_text": response_text,
                "is_ready": sales_analysis.is_ready_to_buy,
                "conversation_stage": sales_analysis.current_stage,
                "langchain_powered": True,
                "keywords_extracted": keywords,
                "products_count": len(combined_products),
                "analysis_confidence": sales_analysis.confidence_level
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error in enhanced conversation processing: {e}")
            # Fallback to original conversation service
            return await self._fallback_to_original_service(message)
    
    async def _extract_keywords_enhanced(self, user_message: str) -> Optional[KeywordExtraction]:
        """Enhanced keyword extraction with LangChain and fallback"""
        try:
            if self.use_langchain:
                return await self.langchain_service.extract_keywords_with_langchain(user_message)
            else:
                # Fallback to original service
                keywords = await self.fallback_service.extract_keywords_with_llm(user_message)
                return KeywordExtraction(
                    keywords=keywords,
                    is_beauty_related=len(keywords) > 0,
                    confidence=0.8 if keywords else 0.2
                )
        except Exception as e:
            self.logger.error(f"❌ Enhanced keyword extraction failed: {e}")
            # Double fallback
            keywords = await self.fallback_service.extract_keywords_with_llm(user_message)
            return KeywordExtraction(
                keywords=keywords,
                is_beauty_related=len(keywords) > 0,
                confidence=0.7
            )
    
    async def _analyze_sales_stage_enhanced(
        self, 
        conversation_history: str, 
        user_message: str, 
        product_info: str
    ) -> SalesStageAnalysis:
        """Enhanced sales stage analysis with LangChain and fallback"""
        try:
            if self.use_langchain:
                return await self.langchain_service.analyze_sales_stage_with_langchain(
                    conversation_history, user_message, product_info
                )
            else:
                # Fallback to original service
                analysis = self.fallback_service.analyze_sales_stage(
                    conversation_history, user_message, product_info
                )
                return self._convert_legacy_analysis(analysis)
        except Exception as e:
            self.logger.error(f"❌ Enhanced sales analysis failed: {e}")
            # Double fallback
            analysis = self.fallback_service.analyze_sales_stage(
                conversation_history, user_message, product_info
            )
            return self._convert_legacy_analysis(analysis)
    
    async def _find_matching_products_enhanced(
        self, 
        keywords: List[str], 
        all_products: List[Dict]
    ) -> List[tuple]:
        """Enhanced product matching with LangChain and fallback"""
        try:
            if self.use_langchain:
                return await self.langchain_service.find_matching_products_with_langchain(
                    keywords, all_products
                )
            else:
                # Fallback to original service
                return self.fallback_service.find_matching_products_with_llm(keywords, all_products)
        except Exception as e:
            self.logger.error(f"❌ Enhanced product matching failed: {e}")
            # Double fallback
            return self.fallback_service.find_matching_products_with_llm(keywords, all_products)
    
    async def _generate_response_enhanced(
        self,
        conversation_history: str,
        user_message: str,
        sales_analysis: SalesStageAnalysis,
        product_info: str,
        customer_state: Dict,
        is_first_interaction: bool
    ) -> ConversationResponse:
        """Enhanced response generation with LangChain and fallback"""
        try:
            if self.use_langchain:
                return await self.langchain_service.generate_response_with_langchain(
                    conversation_history,
                    user_message,
                    sales_analysis,
                    product_info,
                    customer_state,
                    is_first_interaction
                )
            else:
                # Fallback to original service
                response_text, is_ready = self.fallback_service.generate_response(
                    conversation_history, product_info, user_message, is_first_interaction
                )
                return ConversationResponse(
                    response_text=response_text,
                    conversation_stage=sales_analysis.current_stage,
                    recommended_products=sales_analysis.interested_products,
                    next_questions=[],
                    urgency_level="normal"
                )
        except Exception as e:
            self.logger.error(f"❌ Enhanced response generation failed: {e}")
            # Double fallback
            response_text, is_ready = self.fallback_service.generate_response(
                conversation_history, product_info, user_message, is_first_interaction
            )
            return ConversationResponse(
                response_text=response_text,
                conversation_stage=sales_analysis.current_stage,
                recommended_products=sales_analysis.interested_products,
                next_questions=[],
                urgency_level="normal"
            )
    
    async def _handle_off_topic_conversation(self, message: Message, conversation_history: List[Dict]) -> Dict:
        """Handle conversations not related to beauty/personal care"""
        response_text = """Thank you for reaching out! I'm here to help you with beauty and personal care products. 
        
Our collection includes premium perfumes, skincare products, hair care solutions, and grooming essentials from top brands.

What beauty or personal care needs can I assist you with today? 🌟"""
        
        # Save conversation
        updated_conversation = conversation_history + [
            {"role": "user", "content": message.text},
            {"role": "assistant", "content": response_text}
        ]
        mongo_handler.save_conversation(message.sender, updated_conversation)
        
        return {
            "sender": message.sender,
            "product_interested": None,
            "interested_product_ids": [],
            "response_text": response_text,
            "is_ready": False,
            "conversation_stage": "OFF_TOPIC",
            "langchain_powered": True
        }
    
    async def _fallback_to_original_service(self, message: Message) -> Dict:
        """Fallback to original conversation service in case of errors"""
        self.logger.warning("🔄 Falling back to original conversation service")
        
        # Import original service to avoid circular imports
        from app.services.conversation_service import conversation_service
        
        try:
            return await conversation_service.process_message(message)
        except Exception as e:
            self.logger.error(f"❌ Original service also failed: {e}")
            # Final fallback with minimal response
            return {
                "sender": message.sender,
                "product_interested": None,
                "interested_product_ids": [],
                "response_text": "I apologize for the technical difficulty. Please try again or contact our support team.",
                "is_ready": False,
                "conversation_stage": "ERROR",
                "langchain_powered": False
            }
    
    def _convert_legacy_analysis(self, legacy_analysis: Dict) -> SalesStageAnalysis:
        """Convert legacy analysis format to new SalesStageAnalysis"""
        return SalesStageAnalysis(
            current_stage=legacy_analysis.get('current_stage', 'INITIAL_INTEREST'),
            customer_intent=legacy_analysis.get('customer_intent', 'product_inquiry'),
            is_ready_to_buy=legacy_analysis.get('is_ready_to_buy', False),
            confidence_level=legacy_analysis.get('confidence_level', 0.7),
            interested_products=legacy_analysis.get('interested_products', []),
            price_range_mentioned=legacy_analysis.get('price_range_mentioned'),
            prices_shown_in_conversation=legacy_analysis.get('prices_shown_in_conversation', False),
            customer_saw_prices=legacy_analysis.get('customer_saw_prices', False),
            next_action=legacy_analysis.get('next_action', 'understand_needs'),
            stage_transition_reason=legacy_analysis.get('stage_transition_reason', 'Legacy analysis'),
            explicit_purchase_words=legacy_analysis.get('explicit_purchase_words', False),
            requires_price_introduction=legacy_analysis.get('requires_price_introduction', False)
        )
    
    def _get_enhanced_conversation_state(self, sender_id: str) -> Dict:
        """Get enhanced conversation state for user"""
        if sender_id not in self.conversation_states:
            self.conversation_states[sender_id] = {
                "products": [],
                "stage": "INITIAL_INTEREST",
                "langchain_memory": {},
                "interaction_count": 0,
                "last_update": datetime.now().isoformat()
            }
        return self.conversation_states[sender_id]
    
    def _update_enhanced_conversation_state(self, sender_id: str, products: List[Dict], stage: str):
        """Update enhanced conversation state"""
        state = self._get_enhanced_conversation_state(sender_id)
        
        # Add new products, avoiding duplicates
        for product in products:
            if not any(p['id'] == product['id'] for p in state['products']):
                state['products'].append(product)
        
        state['stage'] = stage
        state['interaction_count'] += 1
        state['last_update'] = datetime.now().isoformat()
        
        # Also update LangChain service state
        self.langchain_service.update_conversation_state(sender_id, products, stage)
        
        self.logger.info(f"✅ Enhanced state updated for {sender_id}: {len(state['products'])} products, stage: {stage}")
    
    def _determine_product_interest_enhanced(
        self, 
        sender_id: str, 
        sales_analysis: SalesStageAnalysis, 
        is_ready: bool
    ) -> Optional[str]:
        """Determine product interest using enhanced conversation state"""
        state = self._get_enhanced_conversation_state(sender_id)
        
        # Priority 1: Ready to buy - return products from state
        if is_ready and state['products']:
            if len(state['products']) == 1:
                return state['products'][0]['name']
            else:
                names = [p['name'] for p in state['products']]
                return f"Multiple products: {', '.join(names)}"
        
        # Priority 2: Products from sales analysis
        if sales_analysis.interested_products:
            if len(sales_analysis.interested_products) == 1:
                return sales_analysis.interested_products[0]
            else:
                return f"Multiple products: {', '.join(sales_analysis.interested_products)}"
        
        # Priority 3: Products from conversation state
        if state['products']:
            if len(state['products']) == 1:
                return state['products'][0]['name']
            else:
                names = [p['name'] for p in state['products']]
                return f"Multiple products: {', '.join(names)}"
        
        return None
    
    def _extract_product_ids_enhanced(self, sender_id: str) -> List[str]:
        """Extract product IDs from enhanced conversation state"""
        state = self._get_enhanced_conversation_state(sender_id)
        return [product['id'] for product in state['products']]
    
    def _format_conversation_history(self, conversation: List[Dict]) -> str:
        """Format conversation history for AI context"""
        if not conversation:
            return "No previous conversation."
        
        formatted = []
        for msg in conversation:
            role = "Customer" if msg['role'] == 'user' else "Assistant"
            formatted.append(f"{role}: {msg['content']}")
        
        return "\\n".join(formatted)
    
    def _build_initial_product_info(self, products: List[Dict]) -> str:
        """Build initial product information for analysis"""
        if not products:
            return "Beauty and personal care products available"
        
        info_parts = []
        for product in products[:5]:  # Sample of 5 products
            info_parts.append(f"- {product['name']}: ₹{product['price']}")
        
        return "\\n".join(info_parts)
    
    def _build_enhanced_product_info(self, products: List[Dict]) -> str:
        """Build comprehensive product information"""
        if not products:
            return """Our premium beauty collection includes:
            
🌟 **Captivating Fragrances** - Premium perfumes and body sprays
💫 **Advanced Skincare** - Face washes, moisturizers, and treatments  
✨ **Professional Hair Care** - Shampoos, conditioners, and styling products
🌿 **Natural Beauty Soaps** - Moisturizing and nourishing formulas
💎 **Grooming Essentials** - Deodorants and personal care items

What specific beauty needs can I help you with today?"""
        
        product_details = []
        for product in products:
            # Enhanced price display
            price_info = f"₹{product['price']}"
            if product.get('sale_price') and product['sale_price'] < product['price']:
                savings = product['price'] - product['sale_price']
                price_info = f"₹{product['sale_price']} (Save ₹{savings}!) ~~₹{product['price']}~~"
            
            # Stock status with urgency
            stock_count = product['stock_count']
            if stock_count > 50:
                stock_status = "✅ Well stocked"
            elif stock_count > 10:
                stock_status = "📦 In stock"
            elif stock_count > 0:
                stock_status = f"⚡ Only {stock_count} left - Limited stock!"
            else:
                stock_status = "❌ Out of stock"
            
            # Rating display
            rating = product.get('rating', 0)
            stars = "⭐" * int(rating) + "☆" * (5 - int(rating))
            rating_info = f"{stars} {rating}/5.0 ({product['review_count']} reviews)"
            
            details = f"""
**{product['name']}** (ID: {product['id']})
💰 **Price:** {price_info}
📦 **Availability:** {stock_status}
⭐ **Customer Rating:** {rating_info}
📝 **Description:** {product['description']}
"""
            product_details.append(details.strip())
        
        return "\\n\\n".join(product_details)
    
    def _apply_price_filtering(self, products: List[Dict], price_range: str) -> List[Dict]:
        """Apply price range filtering"""
        try:
            import re
            price_numbers = re.findall(r'(\\d+)', price_range)
            if not price_numbers:
                return products
            
            max_price = int(price_numbers[0])
            filtered = []
            
            for product in products:
                effective_price = product.get('sale_price') or product.get('price', 0)
                if effective_price <= max_price:
                    filtered.append(product)
            
            self.logger.info(f"💰 Price filtered: {len(filtered)}/{len(products)} products under ₹{max_price}")
            return filtered
            
        except Exception as e:
            self.logger.error(f"❌ Price filtering failed: {e}")
            return products

# Initialize the enhanced conversation service
enhanced_conversation_service = EnhancedConversationService()
