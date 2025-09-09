"""
Enhanced Response Generator
==========================

Improved response generation with better consistency and quality.
Addresses the response quality issues identified in testing.
"""

import logging
import json
import hashlib
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
try:
    from langchain_core.output_parsers import PydanticOutputParser
except ImportError:
    from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class ConversationResponse(BaseModel):
    """Enhanced conversation response structure."""
    message: str = Field(description="Main response message")
    tone: str = Field(description="Response tone (friendly, professional, enthusiastic)")
    confidence_level: str = Field(description="Confidence in response (high, medium, low)")
    call_to_action: Optional[str] = Field(description="Clear next step for customer")
    product_recommendations: List[str] = Field(description="Product names mentioned")
    key_information: List[str] = Field(description="Important facts shared")
    conversation_goals: List[str] = Field(description="What this response aims to achieve")

@dataclass
class ResponseContext:
    """Context for response generation."""
    customer_message: str
    sales_stage: str
    is_ready_to_buy: bool
    conversation_history: List[BaseMessage]
    matched_products: List[Any]
    customer_sentiment: str
    conversation_length: int
    previous_topics: List[str]

class EnhancedResponseGenerator:
    """
    Enhanced response generator with improved consistency and quality.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Enhanced response cache with metadata
        self.response_cache = {}
        self.cache_metadata = {}
        self.max_cache_size = 100  # Increased cache size
        
        # Response quality tracking
        self.quality_metrics = {
            'total_responses': 0,
            'cache_hits': 0,
            'generation_times': [],
            'quality_scores': []
        }

        # Stage-specific response templates for consistency
        self.stage_templates = {
            "INITIAL_INTEREST": {
                "greeting_patterns": [
                    "Hi there! I'm excited to help you find the perfect {category} products.",
                    "Welcome! I'd love to help you discover some amazing {category} options.",
                    "Hello! Let's find you some fantastic {category} products that will work perfectly for you."
                ],
                "question_patterns": [
                    "To recommend the best products, could you tell me more about {topic}?",
                    "I'd love to learn more about {topic} to give you personalized recommendations.",
                    "What specific {topic} are you most concerned about?"
                ]
            },
            "PRODUCT_DISCOVERY": {
                "information_patterns": [
                    "Great question! Let me tell you about {product} - it's specifically designed for {benefit}.",
                    "I'd be happy to explain {product}! This {category} is excellent because {benefit}.",
                    "{product} is one of our top recommendations for {concern}, and here's why:"
                ],
                "comparison_patterns": [
                    "Both {product1} and {product2} are excellent choices, but here are the key differences:",
                    "Let me compare these options to help you choose the best fit:",
                    "I can see why you're considering both - let me break down how they differ:"
                ]
            },
            "PRICE_EVALUATION": {
                "value_patterns": [
                    "I understand budget is important! {product} offers excellent value because {reasons}.",
                    "Let me share why {product} is worth the investment - {benefits}.",
                    "Great news! {product} is currently {price}, and here's what makes it worth every penny:"
                ],
                "alternatives_patterns": [
                    "If you're looking for something more budget-friendly, I'd recommend {alternative}.",
                    "Here are some excellent options within your budget that still deliver amazing results:",
                    "I have some fantastic alternatives that might work better for your budget:"
                ]
            },
            "PURCHASE_INTENT": {
                "encouragement_patterns": [
                    "That's a fantastic choice! {product} is going to work wonderfully for you.",
                    "Excellent decision! {product} is one of our customer favorites for good reason.",
                    "I think you'll absolutely love {product} - it's perfect for {benefit}."
                ],
                "guidance_patterns": [
                    "To complete your order for {product}, here's what happens next:",
                    "I'm excited to help you get {product}! Here's how to finalize your purchase:",
                    "Let's get {product} on its way to you. The next step is:"
                ]
            },
            "PURCHASE_CONFIRMATION": {
                "completion_patterns": [
                    "Perfect! I'll help you complete your order for {products}.",
                    "Wonderful! Let's finalize your purchase of {products}.",
                    "Excellent choice! I'll guide you through completing your order."
                ],
                "handover_patterns": [
                    "I'll connect you with our purchase specialist to complete your order.",
                    "Let me transfer you to our checkout team to finalize everything.",
                    "I'll hand you over to our sales team to complete your purchase."
                ]
            }
        }

        # Initialize Azure OpenAI LLM
        try:
            from langchain_openai import AzureChatOpenAI
        except ImportError:
            try:
                from langchain_community.chat_models import AzureChatOpenAI
            except ImportError:
                AzureChatOpenAI = None

        if AzureChatOpenAI:
            from app.core.config import settings
            self.llm = AzureChatOpenAI(
                azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
                azure_deployment=settings.AZURE_OPENAI_DEPLOYMENT,
                openai_api_version=settings.OPENAI_API_VERSION,
                openai_api_key=settings.AZURE_OPENAI_API_KEY,
                temperature=0.3,  # Balanced creativity and consistency
                max_tokens=350    # Optimized token count
            )
        else:
            self.llm = None

        # Enhanced conversation prompt
        self.conversation_prompt = ChatPromptTemplate.from_template("""
        You are Sarah, an expert beauty consultant with 8+ years of experience helping customers find their perfect skincare and beauty products.

        PERSONALITY TRAITS:
        - Warm, friendly, and genuinely enthusiastic about beauty
        - Knowledgeable but not overwhelming - explain things clearly
        - Attentive to customer needs and preferences
        - Professional but personable - make customers feel comfortable
        - Confident in recommendations but respect customer choices

        RESPONSE GUIDELINES:
        
        STAGE-SPECIFIC APPROACH:
        {stage} Stage Focus:
        - INITIAL_INTEREST: Warm welcome, understand needs, ask clarifying questions
        - PRODUCT_DISCOVERY: Detailed product information, benefits, comparisons
        - PRICE_EVALUATION: Value proposition, budget options, justify pricing
        - PURCHASE_INTENT: Encouragement, address concerns, guide toward purchase
        - PURCHASE_CONFIRMATION: Assist with completion, handover to sales team

        CONVERSATION CONTEXT:
        - Customer Message: "{customer_message}"
        - Sales Stage: {stage}
        - Ready to Buy: {ready_to_buy}
        - Customer Sentiment: {sentiment}
        - Conversation Length: {conversation_length} messages
        - Previous Topics: {previous_topics}

        PRODUCT RECOMMENDATIONS:
        {product_info}

        RESPONSE REQUIREMENTS:
        1. CONSISTENCY: Maintain the same helpful, enthusiastic tone throughout
        2. RELEVANCE: Address the customer's specific question or concern directly
        3. CLARITY: Use simple, easy-to-understand language
        4. ENGAGEMENT: Ask follow-up questions to keep the conversation flowing
        5. HELPFULNESS: Provide actionable advice and clear next steps
        6. CONFIDENCE: Be assured in your recommendations while respecting preferences

        RESPONSE STRUCTURE:
        - Start with acknowledgment of their message
        - Provide helpful information or recommendations
        - Include a clear call-to-action or question
        - Keep response length appropriate (2-4 sentences for simple questions, more for complex topics)

        CONVERSATION FLOW RULES:
        - If customer is ready to buy → Guide toward purchase completion
        - If customer has concerns → Address them directly with helpful information
        - If customer is exploring → Provide detailed product information and comparisons
        - If conversation is long (6+ messages) → Consider recommending live agent handover

        {format_instructions}
        """)

        self.response_parser = PydanticOutputParser(pydantic_object=ConversationResponse)

    async def generate_response(self, context: ResponseContext) -> Dict[str, Any]:
        """
        Generate enhanced response with improved consistency.
        """
        try:
            # Check cache first for performance
            cache_key = self._generate_cache_key(context)
            cached_response = self._get_cached_response(cache_key, context)
            
            if cached_response:
                self.quality_metrics['cache_hits'] += 1
                self.logger.info("💨 Using cached response for similar context")
                return cached_response

            # Generate new response
            start_time = datetime.now()
            
            if self.llm:
                response = await self._generate_with_llm(context)
            else:
                response = self._generate_with_templates(context)
            
            generation_time = (datetime.now() - start_time).total_seconds()
            self.quality_metrics['generation_times'].append(generation_time)
            
            # Enhance response with metadata
            enhanced_response = self._enhance_response(response, context)
            
            # Cache the response
            self._cache_response(cache_key, enhanced_response, context)
            
            # Update quality metrics
            self.quality_metrics['total_responses'] += 1
            quality_score = self._assess_response_quality(enhanced_response, context)
            self.quality_metrics['quality_scores'].append(quality_score)
            
            self.logger.info(f"✨ Generated response in {generation_time:.2f}s, quality: {quality_score:.2f}")
            return enhanced_response
            
        except Exception as e:
            self.logger.error(f"❌ Response generation failed: {e}")
            return self._generate_fallback_response(context)

    async def _generate_with_llm(self, context: ResponseContext) -> ConversationResponse:
        """
        Generate response using LLM with enhanced prompting.
        """
        try:
            # Format product information
            product_info = self._format_product_info(context.matched_products)
            
            # Format previous topics
            previous_topics = ", ".join(context.previous_topics) if context.previous_topics else "None"
            
            chain = self.conversation_prompt | self.llm | self.response_parser
            
            response = await chain.ainvoke({
                "customer_message": context.customer_message,
                "stage": context.sales_stage,
                "ready_to_buy": context.is_ready_to_buy,
                "sentiment": context.customer_sentiment,
                "conversation_length": context.conversation_length,
                "previous_topics": previous_topics,
                "product_info": product_info,
                "format_instructions": self.response_parser.get_format_instructions()
            })

            self.logger.info(f"🤖 LLM generated {context.sales_stage} response")
            return response

        except Exception as e:
            self.logger.error(f"❌ LLM generation failed: {e}")
            return self._generate_with_templates(context)

    def _generate_with_templates(self, context: ResponseContext) -> ConversationResponse:
        """
        Generate response using templates for consistency.
        """
        stage = context.sales_stage
        templates = self.stage_templates.get(stage, self.stage_templates["INITIAL_INTEREST"])
        
        # Select appropriate template based on context
        if context.matched_products:
            product_name = context.matched_products[0].product.get('name', 'this product')
            category = context.matched_products[0].product.get('category', 'skincare')
        else:
            product_name = "our products"
            category = "beauty"
        
        # Generate message based on stage
        if stage == "INITIAL_INTEREST":
            if context.conversation_length == 1:
                message = templates["greeting_patterns"][0].format(category=category)
            else:
                message = templates["question_patterns"][0].format(topic="your skin concerns")
        
        elif stage == "PRODUCT_DISCOVERY":
            if context.matched_products:
                benefit = context.matched_products[0].match_reasons[0] if hasattr(context.matched_products[0], 'match_reasons') else "your needs"
                message = templates["information_patterns"][0].format(
                    product=product_name, 
                    category=category,
                    benefit=benefit
                )
            else:
                message = "I'd be happy to tell you more about our products!"
        
        elif stage == "PRICE_EVALUATION":
            price = context.matched_products[0].product.get('price', '$25') if context.matched_products else '$25'
            message = templates["value_patterns"][0].format(
                product=product_name,
                price=price,
                reasons="it delivers excellent results"
            )
        
        elif stage == "PURCHASE_INTENT":
            message = templates["encouragement_patterns"][0].format(
                product=product_name,
                benefit="your specific needs"
            )
        
        elif stage == "PURCHASE_CONFIRMATION":
            message = templates["completion_patterns"][0].format(products=product_name)
        
        else:
            message = "I'm here to help you find the perfect beauty products!"

        # Add call-to-action
        if context.is_ready_to_buy:
            call_to_action = "Would you like me to help you complete your purchase?"
        elif context.conversation_length >= 6:
            call_to_action = "Would you like to speak with one of our beauty specialists?"
        else:
            call_to_action = "What other questions can I answer for you?"

        return ConversationResponse(
            message=message,
            tone="friendly" if context.customer_sentiment == "positive" else "professional",
            confidence_level="high",
            call_to_action=call_to_action,
            product_recommendations=[product_name] if context.matched_products else [],
            key_information=[f"Recommendation for {category} products"],
            conversation_goals=[f"Help customer in {stage} stage"]
        )

    def _enhance_response(self, response: ConversationResponse, context: ResponseContext) -> Dict[str, Any]:
        """
        Enhance response with additional metadata and optimizations.
        """
        # Create enhanced response structure
        enhanced = {
            "message": response.message,
            "metadata": {
                "stage": context.sales_stage,
                "confidence": response.confidence_level,
                "tone": response.tone,
                "ready_to_buy": context.is_ready_to_buy,
                "conversation_length": context.conversation_length,
                "generation_method": "llm" if self.llm else "template"
            },
            "recommendations": {
                "products": response.product_recommendations,
                "next_action": response.call_to_action,
                "key_points": response.key_information
            },
            "conversation_context": {
                "customer_sentiment": context.customer_sentiment,
                "sales_progression": True,
                "engagement_level": "high" if len(response.message) > 100 else "moderate"
            }
        }
        
        # Add handover recommendation if needed
        if self._should_recommend_handover(context):
            enhanced["handover_recommendation"] = {
                "recommended": True,
                "reason": "Customer ready for purchase completion" if context.is_ready_to_buy 
                         else "Complex conversation requiring specialist assistance",
                "urgency": "high" if context.is_ready_to_buy else "medium"
            }
        
        return enhanced

    def _generate_cache_key(self, context: ResponseContext) -> str:
        """
        Generate cache key for similar contexts.
        """
        # Create key based on important context elements
        key_elements = [
            context.sales_stage,
            str(context.is_ready_to_buy),
            context.customer_sentiment,
            str(context.conversation_length // 3),  # Group by conversation length ranges
            context.customer_message[:50]  # First 50 chars for similarity
        ]
        
        # Add product categories for context
        if context.matched_products:
            categories = [p.product.get('category', '') for p in context.matched_products[:2]]
            key_elements.extend(categories)
        
        key_string = "|".join(key_elements)
        return hashlib.md5(key_string.encode()).hexdigest()

    def _get_cached_response(self, cache_key: str, context: ResponseContext) -> Optional[Dict[str, Any]]:
        """
        Get cached response if appropriate.
        """
        if cache_key in self.response_cache:
            cached = self.response_cache[cache_key]
            metadata = self.cache_metadata.get(cache_key, {})
            
            # Check if cache is still fresh (within last hour)
            cache_age = datetime.now() - metadata.get('timestamp', datetime.now())
            if cache_age.total_seconds() < 3600:  # 1 hour
                # Personalize cached response
                personalized = self._personalize_cached_response(cached, context)
                return personalized
        
        return None

    def _cache_response(self, cache_key: str, response: Dict[str, Any], context: ResponseContext):
        """
        Cache response with metadata.
        """
        # Manage cache size
        if len(self.response_cache) >= self.max_cache_size:
            # Remove oldest entries
            oldest_keys = sorted(
                self.cache_metadata.keys(),
                key=lambda k: self.cache_metadata[k].get('timestamp', datetime.min)
            )[:10]
            
            for key in oldest_keys:
                self.response_cache.pop(key, None)
                self.cache_metadata.pop(key, None)
        
        # Cache the response
        self.response_cache[cache_key] = response.copy()
        self.cache_metadata[cache_key] = {
            'timestamp': datetime.now(),
            'stage': context.sales_stage,
            'usage_count': 1
        }

    def _personalize_cached_response(self, cached_response: Dict[str, Any], context: ResponseContext) -> Dict[str, Any]:
        """
        Personalize cached response for current context.
        """
        personalized = cached_response.copy()
        
        # Update metadata
        personalized["metadata"]["conversation_length"] = context.conversation_length
        personalized["metadata"]["ready_to_buy"] = context.is_ready_to_buy
        
        # Add products if available
        if context.matched_products:
            product_names = [p.product.get('name', 'Product') for p in context.matched_products[:2]]
            personalized["recommendations"]["products"] = product_names
        
        return personalized

    def _assess_response_quality(self, response: Dict[str, Any], context: ResponseContext) -> float:
        """
        Assess response quality for metrics.
        """
        score = 0.8  # Base score
        
        # Length appropriateness
        message_length = len(response.get("message", ""))
        if 50 <= message_length <= 300:
            score += 0.1
        
        # Has call to action
        if response.get("recommendations", {}).get("next_action"):
            score += 0.05
        
        # Product recommendations present when needed
        if context.matched_products and response.get("recommendations", {}).get("products"):
            score += 0.05
        
        return min(score, 1.0)

    def _should_recommend_handover(self, context: ResponseContext) -> bool:
        """
        Determine if human handover should be recommended.
        """
        return (
            (context.is_ready_to_buy and context.sales_stage == "PURCHASE_CONFIRMATION") or
            (context.conversation_length >= 8) or
            (context.customer_sentiment == "negative" and context.conversation_length >= 4)
        )

    def _format_product_info(self, matched_products: List[Any]) -> str:
        """
        Format product information for prompt.
        """
        if not matched_products:
            return "No specific products matched for this query."
        
        formatted = []
        for i, match in enumerate(matched_products[:3]):
            product = match.product
            info = f"{i+1}. {product.get('name', 'Product')} by {product.get('brand', 'Brand')}"
            info += f" - ${product.get('price', 'N/A')}"
            
            if hasattr(match, 'match_reasons'):
                info += f" (Match: {', '.join(match.match_reasons[:2])})"
            
            formatted.append(info)
        
        return "\n".join(formatted)

    def _generate_fallback_response(self, context: ResponseContext) -> Dict[str, Any]:
        """
        Generate simple fallback response when all else fails.
        """
        stage_messages = {
            "INITIAL_INTEREST": "Hi! I'm here to help you find the perfect beauty products. What are you looking for today?",
            "PRODUCT_DISCOVERY": "I'd be happy to tell you more about our products! What specific information would you like?",
            "PRICE_EVALUATION": "I understand you'd like to know about pricing. Let me share some great value options with you.",
            "PURCHASE_INTENT": "That sounds like a great choice! I can help guide you through your purchase.",
            "PURCHASE_CONFIRMATION": "Perfect! I'll help you complete your order. Let me connect you with our sales team."
        }
        
        message = stage_messages.get(context.sales_stage, "I'm here to help you with your beauty needs!")
        
        return {
            "message": message,
            "metadata": {
                "stage": context.sales_stage,
                "confidence": "medium",
                "tone": "friendly",
                "ready_to_buy": context.is_ready_to_buy,
                "conversation_length": context.conversation_length,
                "generation_method": "fallback"
            },
            "recommendations": {
                "products": [],
                "next_action": "How can I help you further?",
                "key_points": ["Ready to assist with your beauty needs"]
            },
            "conversation_context": {
                "customer_sentiment": context.customer_sentiment,
                "sales_progression": True,
                "engagement_level": "moderate"
            }
        }

    def get_quality_metrics(self) -> Dict[str, Any]:
        """
        Get current quality metrics.
        """
        avg_generation_time = sum(self.quality_metrics['generation_times'][-10:]) / max(len(self.quality_metrics['generation_times'][-10:]), 1)
        avg_quality_score = sum(self.quality_metrics['quality_scores'][-10:]) / max(len(self.quality_metrics['quality_scores'][-10:]), 1)
        cache_hit_rate = self.quality_metrics['cache_hits'] / max(self.quality_metrics['total_responses'], 1)
        
        return {
            "total_responses": self.quality_metrics['total_responses'],
            "cache_hit_rate": cache_hit_rate,
            "avg_generation_time": avg_generation_time,
            "avg_quality_score": avg_quality_score,
            "cache_size": len(self.response_cache)
        }

# Create enhanced response generator instance
enhanced_response_generator = EnhancedResponseGenerator()
