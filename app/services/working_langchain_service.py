"""
Working LangChain Conversation Service
=====================================

A simplified, working LangChain-based conversation service that integrates
with the existing AI service while adding LangChain memory and structured outputs.
"""

import logging
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime

# LangChain imports that we know work
from langchain.chains import LLMChain
from langchain.memory import ConversationBufferWindowMemory
from langchain_core.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage, AIMessage

# Pydantic models for structured outputs
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Structured output models
class KeywordExtraction(BaseModel):
    """Structured output for keyword extraction"""
    keywords: List[str] = Field(description="List of relevant beauty/personal care keywords")
    is_beauty_related: bool = Field(description="Whether the message is related to beauty/personal care")
    confidence: float = Field(description="Confidence score for keyword relevance")

class SalesStageAnalysis(BaseModel):
    """Structured output for sales stage analysis"""
    current_stage: str = Field(description="Current sales funnel stage")
    customer_intent: str = Field(description="Primary customer intent")
    is_ready_to_buy: bool = Field(description="Whether customer is ready to purchase")
    confidence_level: float = Field(description="Confidence in analysis")
    interested_products: List[str] = Field(description="Products customer is interested in")
    price_range_mentioned: Optional[str] = Field(description="Budget range if mentioned", default=None)
    prices_shown_in_conversation: bool = Field(description="Whether prices have been shown")
    customer_saw_prices: bool = Field(description="Whether customer acknowledged prices")
    next_action: str = Field(description="Recommended next action")
    stage_transition_reason: str = Field(description="Reason for current stage determination")
    explicit_purchase_words: bool = Field(description="Whether explicit purchase language was used")
    requires_price_introduction: bool = Field(description="Whether prices need to be shown")

class ConversationResponse(BaseModel):
    """Structured output for conversation responses"""
    response_text: str = Field(description="Generated response text")
    conversation_stage: str = Field(description="Current conversation stage")
    recommended_products: List[str] = Field(description="Products to recommend")
    next_questions: List[str] = Field(default_factory=list, description="Suggested follow-up questions")
    urgency_level: str = Field(default="normal", description="Response urgency level")

class WorkingLangChainService:
    """
    A working LangChain service that integrates with existing AI service
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.conversation_states = {}  # User memory states
        
        # Connect to existing AI service
        try:
            from app.services.ai_service import ai_service
            self.ai_service = ai_service
            self.logger.info("✅ Connected to existing AI service")
        except ImportError as e:
            self.logger.error(f"❌ Failed to connect to AI service: {e}")
            self.ai_service = None
        
        self.logger.info("✅ Working LangChain service initialized")

    def get_user_memory(self, user_id: str) -> ConversationBufferWindowMemory:
        """Get or create memory for a user"""
        if user_id not in self.conversation_states:
            self.conversation_states[user_id] = {
                "memory": ConversationBufferWindowMemory(
                    k=10,  # Remember last 10 exchanges
                    return_messages=True,
                    memory_key="chat_history"
                ),
                "products": [],
                "stage": "INITIAL_INTEREST"
            }
        return self.conversation_states[user_id]["memory"]

    def extract_keywords_with_langchain(self, user_message: str) -> KeywordExtraction:
        """Extract keywords using LangChain-enhanced approach"""
        try:
            # Use existing AI service but wrap in LangChain structure
            if self.ai_service:
                # Get keywords from existing service
                keywords = []
                try:
                    # Use fallback for now to avoid async issues in sync context
                    keywords = self._extract_keywords_fallback(user_message)
                except:
                    # Fallback sync call
                    keywords = self._extract_keywords_fallback(user_message)
                
                # Determine if beauty-related
                beauty_keywords = [
                    'beauty', 'skincare', 'hair', 'perfume', 'soap', 'shampoo', 
                    'cream', 'moisturizer', 'face wash', 'deodorant', 'oil'
                ]
                
                message_lower = user_message.lower()
                is_beauty_related = any(bk in message_lower for bk in beauty_keywords) or len(keywords) > 0
                
                confidence = 0.8 if keywords and is_beauty_related else 0.3
                
                return KeywordExtraction(
                    keywords=keywords,
                    is_beauty_related=is_beauty_related,
                    confidence=confidence
                )
            else:
                # Fallback keyword extraction
                return self._extract_keywords_fallback_structured(user_message)
                
        except Exception as e:
            self.logger.error(f"Error in keyword extraction: {e}")
            return KeywordExtraction(keywords=[], is_beauty_related=False, confidence=0.0)

    def _extract_keywords_fallback(self, user_message: str) -> List[str]:
        """Simple fallback keyword extraction"""
        beauty_terms = [
            'perfume', 'shampoo', 'soap', 'cream', 'oil', 'moisturizer',
            'face wash', 'hair', 'skin', 'beauty', 'care', 'deodorant'
        ]
        
        message_lower = user_message.lower()
        found_keywords = [term for term in beauty_terms if term in message_lower]
        
        # Add purchase intent words
        purchase_words = ['buy', 'purchase', 'order', 'need', 'want', 'looking']
        found_keywords.extend([word for word in purchase_words if word in message_lower])
        
        return found_keywords[:5]  # Limit to 5 keywords

    def _extract_keywords_fallback_structured(self, user_message: str) -> KeywordExtraction:
        """Structured fallback keyword extraction"""
        keywords = self._extract_keywords_fallback(user_message)
        is_beauty_related = len(keywords) > 0
        confidence = 0.6 if is_beauty_related else 0.2
        
        return KeywordExtraction(
            keywords=keywords,
            is_beauty_related=is_beauty_related,
            confidence=confidence
        )

    async def analyze_sales_stage_with_langchain(self, conversation_history: str, user_message: str, product_info: str = "") -> SalesStageAnalysis:
        """Analyze sales stage using LangChain-enhanced approach"""
        try:
            # Use existing AI service but wrap in LangChain structure
            if self.ai_service:
                # Get analysis from existing service properly
                try:
                    analysis_result = await self.ai_service.analyze_sales_stage(conversation_history, user_message, product_info)
                    
                    # Handle the result properly (it might be a dict already)
                    if isinstance(analysis_result, dict):
                        analysis = analysis_result
                    else:
                        # If it's some other format, convert to dict
                        analysis = {}
                        
                except Exception as e:
                    self.logger.error(f"Sales stage analysis failed: {e}")
                    return self._analyze_sales_stage_fallback(user_message)
                
                # Convert to structured output
                return SalesStageAnalysis(
                    current_stage=analysis.get('current_stage', 'INITIAL_INTEREST'),
                    customer_intent=analysis.get('customer_intent', 'product_inquiry'),
                    is_ready_to_buy=analysis.get('is_ready_to_buy', False),
                    confidence_level=analysis.get('confidence_level', 0.7),
                    interested_products=analysis.get('interested_products', []),
                    price_range_mentioned=analysis.get('price_range_mentioned'),
                    prices_shown_in_conversation=analysis.get('prices_shown_in_conversation', False),
                    customer_saw_prices=analysis.get('customer_saw_prices', False),
                    next_action=analysis.get('next_action', 'understand_needs'),
                    stage_transition_reason=analysis.get('stage_transition_reason', 'Analysis complete'),
                    explicit_purchase_words=analysis.get('explicit_purchase_words', False),
                    requires_price_introduction=analysis.get('requires_price_introduction', False)
                )
            else:
                # Fallback analysis
                return self._analyze_sales_stage_fallback(user_message)
                
        except Exception as e:
            self.logger.error(f"Error in sales stage analysis: {e}")
            return self._analyze_sales_stage_fallback(user_message)

    def _analyze_sales_stage_fallback(self, user_message: str) -> SalesStageAnalysis:
        """Simple fallback sales analysis"""
        message_lower = user_message.lower()
        
        # Simple purchase detection
        purchase_confirmations = ['i\'ll take', 'yes, i\'ll buy', 'i\'ll purchase', 'i want to buy']
        purchase_intents = ['buy', 'purchase', 'order']
        
        is_purchase_confirmation = any(phrase in message_lower for phrase in purchase_confirmations)
        has_purchase_intent = any(word in message_lower for word in purchase_intents)
        
        if is_purchase_confirmation:
            stage = "PURCHASE_CONFIRMATION"
            is_ready = True
            action = "confirm_purchase"
        elif has_purchase_intent:
            stage = "PURCHASE_INTENT"
            is_ready = False
            action = "show_prices"
        else:
            stage = "INITIAL_INTEREST"
            is_ready = False
            action = "understand_needs"
        
        return SalesStageAnalysis(
            current_stage=stage,
            customer_intent="purchase_confirmation" if is_purchase_confirmation else "product_inquiry",
            is_ready_to_buy=is_ready,
            confidence_level=0.7,
            interested_products=[],
            prices_shown_in_conversation=False,
            customer_saw_prices=False,
            next_action=action,
            stage_transition_reason="Simple keyword-based analysis",
            explicit_purchase_words=is_purchase_confirmation,
            requires_price_introduction=not is_ready
        )

    async def find_matching_products_with_langchain(self, keywords: List[str], all_products: List[Dict]) -> List[tuple]:
        """Find matching products using LangChain-enhanced approach"""
        try:
            # Use existing AI service for product matching
            if self.ai_service:
                matches = await self.ai_service.find_matching_products_with_llm(keywords, all_products)
                return matches
            else:
                # Simple fallback product matching
                return self._find_products_fallback(keywords, all_products)
                
        except Exception as e:
            self.logger.error(f"Error in product matching: {e}")
            return self._find_products_fallback(keywords, all_products)

    def _find_products_fallback(self, keywords: List[str], all_products: List[Dict]) -> List[tuple]:
        """Simple fallback product matching"""
        matches = []
        
        for product in all_products[:20]:  # Limit for performance
            product_name = product.get('name', '').lower()
            product_tags = product.get('product_tag', [])
            
            score = 60.0  # Base score
            
            # Check keyword matches
            for keyword in keywords:
                if keyword.lower() in product_name:
                    score += 15.0
                elif any(keyword.lower() in tag.lower() for tag in product_tags):
                    score += 10.0
            
            if score >= 70:
                matches.append((product, score))
        
        # Sort by score and return top 5
        return sorted(matches, key=lambda x: x[1], reverse=True)[:5]

    async def generate_response_with_langchain(self, conversation_history: str, user_message: str,
                                             sales_analysis: SalesStageAnalysis, product_info: str,
                                             user_id: str) -> ConversationResponse:
        """Generate response using LangChain-enhanced approach"""
        try:
            # Add to user memory
            memory = self.get_user_memory(user_id)
            memory.chat_memory.add_user_message(user_message)
            
            # Use existing AI service for response generation
            if self.ai_service:
                # Call the async response generation properly
                try:
                    response_result = await self.ai_service.generate_response(
                        conversation_history=conversation_history,
                        product_info=product_info,
                        user_message=user_message,
                        is_first_interaction=len(conversation_history) < 50
                    )
                    
                    # Handle tuple or string response
                    if isinstance(response_result, tuple):
                        response_text, is_ready = response_result
                    else:
                        response_text = response_result
                        is_ready = False
                        
                except Exception as e:
                    self.logger.error(f"AI service call failed: {e}")
                    response_text = self._generate_fallback_response(user_message, sales_analysis)
                    is_ready = False
                
                # Add to memory
                memory.chat_memory.add_ai_message(response_text)
                
                return ConversationResponse(
                    response_text=response_text,
                    conversation_stage=sales_analysis.current_stage,
                    recommended_products=sales_analysis.interested_products,
                    next_questions=["Would you like more details?", "Any specific preferences?"],
                    urgency_level="high" if is_ready else "normal"
                )
            else:
                # Fallback response
                response_text = self._generate_fallback_response(user_message, sales_analysis)
                memory.chat_memory.add_ai_message(response_text)
                
                return ConversationResponse(
                    response_text=response_text,
                    conversation_stage=sales_analysis.current_stage,
                    recommended_products=[],
                    next_questions=[],
                    urgency_level="normal"
                )
                
        except Exception as e:
            self.logger.error(f"Error in response generation: {e}")
            return ConversationResponse(
                response_text="I'd be happy to help you find the perfect beauty and personal care products! What can I assist you with today?",
                conversation_stage="INITIAL_INTEREST",
                recommended_products=[],
                next_questions=[],
                urgency_level="normal"
            )

    def _generate_fallback_response(self, user_message: str, sales_analysis: SalesStageAnalysis) -> str:
        """Generate a simple fallback response"""
        if sales_analysis.is_ready_to_buy:
            return "Thank you for your interest! I'd be happy to help you with your purchase. Let me connect you with our ordering team."
        elif sales_analysis.current_stage == "PURCHASE_INTENT":
            return "Great! I can see you're interested in making a purchase. Let me show you our products with pricing details."
        else:
            return f"Thank you for your message! I'd be happy to help you find the perfect beauty and personal care products. What specific products are you looking for?"

    def update_conversation_memory(self, sender_id: str, user_message: str, ai_response: str):
        """Update conversation memory for user"""
        memory = self.get_user_memory(sender_id)
        memory.chat_memory.add_user_message(user_message)
        memory.chat_memory.add_ai_message(ai_response)

    def get_conversation_state(self, sender_id: str) -> Dict:
        """Get conversation state for user"""
        if sender_id not in self.conversation_states:
            self.get_user_memory(sender_id)  # This will create the state
        return self.conversation_states[sender_id]

    def update_conversation_state(self, sender_id: str, products: List[Dict], stage: str):
        """Update conversation state with products and stage"""
        state = self.get_conversation_state(sender_id)
        
        # Add new products, avoiding duplicates
        for product in products:
            if not any(p.get('id') == product.get('id') for p in state['products']):
                state['products'].append(product)
        
        state['stage'] = stage
        self.logger.info(f"✅ Updated state for {sender_id}: {len(state['products'])} products, stage: {stage}")

# Create the working service instance
langchain_conversation_service = WorkingLangChainService()
