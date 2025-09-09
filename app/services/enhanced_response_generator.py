"""
Enhanced Response Generator
==========================

Advanced LangChain-based response generation with multiple techniques:
1. Chain-of-Thought reasoning
2. Multi-stage response refinement
3. Context-aware personalization
4. Quality assurance validation
5. Response optimization
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.output_parsers import PydanticOutputParser, StrOutputParser
from langchain.chains import LLMChain, SequentialChain
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class ResponseQuality(BaseModel):
    """Model for response quality assessment."""
    is_helpful: bool = Field(description="Response addresses customer needs")
    is_conversational: bool = Field(description="Natural conversational tone")
    shows_expertise: bool = Field(description="Demonstrates product knowledge")
    encourages_engagement: bool = Field(description="Invites further conversation")
    is_personalized: bool = Field(description="Tailored to customer context")
    quality_score: float = Field(description="Overall quality score 0-10")
    improvements: List[str] = Field(description="Suggested improvements")

class EnhancedResponse(BaseModel):
    """Model for enhanced response generation."""
    response_text: str = Field(description="Generated response text")
    reasoning: str = Field(description="Chain of thought reasoning")
    confidence_level: float = Field(description="Confidence in response quality")
    personalization_elements: List[str] = Field(description="Personalization used")
    call_to_action: str = Field(description="Next step for customer")

class EnhancedResponseGenerator:
    """
    Advanced response generator using multiple LangChain techniques.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Add response caching for performance
        self.response_cache = {}
        self.cache_hits = 0
        self.total_requests = 0

        # Initialize Azure OpenAI LLM
        try:
            from langchain_openai import AzureChatOpenAI
        except ImportError:
            try:
                from langchain_community.chat_models import AzureChatOpenAI
            except ImportError:
                try:
                    from langchain.chat_models import AzureChatOpenAI
                except ImportError:
                    self.logger.error("AzureChatOpenAI not available - using fallback mode")
                    AzureChatOpenAI = None

        if AzureChatOpenAI:
            from app.core.config import settings
            self.llm = AzureChatOpenAI(
                azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
                azure_deployment=settings.AZURE_OPENAI_DEPLOYMENT,
                openai_api_version=settings.OPENAI_API_VERSION,
                openai_api_key=settings.AZURE_OPENAI_API_KEY,
                temperature=0.3,  # Slightly higher for more creativity
                max_tokens=400  # Further reduced for faster response times
            )
            
            # High-quality LLM for refinement
            self.quality_llm = AzureChatOpenAI(
                azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
                azure_deployment=settings.AZURE_OPENAI_DEPLOYMENT,
                openai_api_version=settings.OPENAI_API_VERSION,
                openai_api_key=settings.AZURE_OPENAI_API_KEY,
                temperature=0.1,  # Lower temperature for quality assessment
                max_tokens=200  # Further reduced for faster quality assessment
            )
        else:
            self.llm = None
            self.quality_llm = None

        self._initialize_chains()

    def _initialize_chains(self):
        """Initialize LangChain chains for multi-stage processing."""
        
        # Chain 1: Initial Response Generation with Chain-of-Thought
        self.initial_response_prompt = ChatPromptTemplate.from_template("""
        You are an expert beauty and personal care consultant. Generate a helpful response using Chain-of-Thought reasoning.

        BUSINESS CONTEXT: We are a premium personal care e-commerce platform offering authentic beauty and grooming products from international brands (Lux, Dove, Pantene, Head & Shoulders) and local manufacturers (Keya Seth, Tibbet).

        CONVERSATION CONTEXT:
        Previous conversation: {conversation_history}
        Customer's current message: {user_message}
        Sales stage: {sales_stage}
        Available products: {product_info}
        First interaction: {is_first_interaction}

        CHAIN-OF-THOUGHT REASONING:
        1. Customer Analysis: What does the customer need? What stage are they at?
        2. Product Matching: Which products best match their needs?
        3. Response Strategy: How should I respond to move them forward?
        4. Personalization: How can I make this response feel personal?
        5. Value Addition: What value can I provide beyond just product info?

        RESPONSE REQUIREMENTS:
        - Be conversational and natural (avoid robotic language)
        - Show genuine enthusiasm for helping
        - Provide specific product recommendations when relevant
        - Include clear next steps or call-to-action
        - Demonstrate expertise without being pushy
        - Keep response between 150-300 words
        - Match the customer's communication style

        REASONING (Think step by step):
        Let me analyze this step by step:
        1. Customer Analysis: [Analyze customer needs and stage]
        2. Product Strategy: [Determine which products to mention]
        3. Response Approach: [Choose conversation style and tone]
        4. Value Creation: [What unique value can I provide]

        Based on my analysis, here's my response:

        RESPONSE: [Your natural, conversational response here]
        """)

        # Chain 2: Quality Assessment
        self.quality_assessment_prompt = ChatPromptTemplate.from_template("""
        Assess the quality of this customer service response:

        CUSTOMER MESSAGE: {user_message}
        AI RESPONSE: {response_text}
        CONVERSATION CONTEXT: {conversation_history}

        Evaluate the response on these criteria:
        1. Helpfulness: Does it address the customer's needs?
        2. Conversational tone: Does it sound natural and friendly?
        3. Expertise: Does it demonstrate product knowledge?
        4. Engagement: Does it encourage further conversation?
        5. Personalization: Is it tailored to this specific customer?

        Rate each criterion (true/false) and provide an overall quality score (0-10).
        List specific improvements if score < 8.

        {format_instructions}
        """)

        # Chain 3: Response Refinement
        self.refinement_prompt = ChatPromptTemplate.from_template("""
        Improve this customer service response based on the quality assessment:

        ORIGINAL RESPONSE: {original_response}
        QUALITY ASSESSMENT: {quality_assessment}
        CUSTOMER MESSAGE: {user_message}
        SALES STAGE: {sales_stage}

        IMPROVEMENT GUIDELINES:
        - Make it more conversational and natural
        - Add personal touches and enthusiasm
        - Ensure clear value proposition
        - Include compelling call-to-action
        - Keep the same core information but enhance delivery
        - Maintain professional yet friendly tone
        - Make it feel like advice from a trusted friend

        ENHANCED RESPONSE:
        """)

        # Initialize parsers
        self.quality_parser = PydanticOutputParser(pydantic_object=ResponseQuality)
        self.str_parser = StrOutputParser()

    async def generate_enhanced_response(self,
                                       conversation_history: str,
                                       user_message: str,
                                       product_info: str,
                                       sales_stage: str = "INITIAL_INTEREST",
                                       is_first_interaction: bool = False) -> Dict[str, Any]:
        """
        Generate an enhanced response using multi-stage chain processing.
        
        Returns:
            Dict containing response, reasoning, and quality metrics
        """
        try:
            self.total_requests += 1
            
            # Check cache first for performance
            cache_key = f"{user_message[:50]}_{sales_stage}_{len(product_info)}"
            if cache_key in self.response_cache:
                self.cache_hits += 1
                self.logger.info(f"🚀 Cache hit! Performance boost ({self.cache_hits}/{self.total_requests})")
                return self.response_cache[cache_key]
            
            if not self.llm:
                return self._fallback_response(user_message, product_info)

            # Stage 1: Generate initial response with Chain-of-Thought
            initial_chain = self.initial_response_prompt | self.llm | self.str_parser
            
            initial_response = await initial_chain.ainvoke({
                "conversation_history": conversation_history,
                "user_message": user_message,
                "sales_stage": sales_stage,
                "product_info": product_info,
                "is_first_interaction": is_first_interaction
            })

            # Extract just the response part (after "RESPONSE:")
            if "RESPONSE:" in initial_response:
                response_text = initial_response.split("RESPONSE:")[-1].strip()
            else:
                response_text = initial_response.strip()

            self.logger.info(f"🔗 Initial response generated: {len(response_text)} characters")

            # Stage 2: Quality Assessment
            quality_chain = self.quality_assessment_prompt | self.quality_llm | self.quality_parser
            
            quality_assessment = await quality_chain.ainvoke({
                "user_message": user_message,
                "response_text": response_text,
                "conversation_history": conversation_history,
                "format_instructions": self.quality_parser.get_format_instructions()
            })

            self.logger.info(f"📊 Quality score: {quality_assessment.quality_score}/10")

            # Stage 3: Refinement (if quality score < 8)
            final_response = response_text
            if quality_assessment.quality_score < 8.0:
                self.logger.info("🔧 Refining response for better quality...")
                
                refinement_chain = self.refinement_prompt | self.llm | self.str_parser
                
                final_response = await refinement_chain.ainvoke({
                    "original_response": response_text,
                    "quality_assessment": quality_assessment.dict(),
                    "user_message": user_message,
                    "sales_stage": sales_stage
                })

                self.logger.info("✨ Response refinement completed")

            # Extract reasoning from initial response
            reasoning = ""
            if "REASONING" in initial_response and "RESPONSE:" in initial_response:
                reasoning_section = initial_response.split("REASONING")[1].split("RESPONSE:")[0]
                reasoning = reasoning_section.strip()

            result = {
                "response_text": final_response.strip(),
                "reasoning": reasoning,
                "quality_score": quality_assessment.quality_score,
                "quality_assessment": quality_assessment.dict(),
                "was_refined": quality_assessment.quality_score < 8.0,
                "confidence_level": min(quality_assessment.quality_score / 10.0, 1.0)
            }
            
            # Cache the result for performance (keep cache small)
            if len(self.response_cache) < 50:  # Limit cache size
                self.response_cache[cache_key] = result
            
            return result

        except Exception as e:
            self.logger.error(f"Error in enhanced response generation: {e}")
            return self._fallback_response(user_message, product_info)

    def _fallback_response(self, user_message: str, product_info: str) -> Dict[str, Any]:
        """Fallback response when LLM is not available."""
        response = f"Thank you for your message! I'd be happy to help you find the right products. "
        
        if "buy" in user_message.lower() or "purchase" in user_message.lower():
            response += "I can see you're interested in making a purchase. Let me connect you with our team to help complete your order."
        elif "price" in user_message.lower() or "cost" in user_message.lower():
            response += "I understand you'd like to know about pricing. Our products are competitively priced and offer great value for quality."
        else:
            response += "Based on what you're looking for, I can recommend some great products that would suit your needs perfectly."

        return {
            "response_text": response,
            "reasoning": "Fallback mode - LLM not available",
            "quality_score": 6.0,
            "was_refined": False,
            "confidence_level": 0.6
        }

    async def generate_contextual_recommendations(self,
                                                customer_profile: Dict[str, Any],
                                                conversation_history: str,
                                                available_products: List[Dict]) -> List[str]:
        """Generate personalized product recommendations."""
        try:
            if not self.llm:
                return ["Based on your needs, I recommend exploring our premium skincare collection."]

            recommendation_prompt = ChatPromptTemplate.from_template("""
            Generate 3 personalized product recommendations:

            CUSTOMER PROFILE: {customer_profile}
            CONVERSATION: {conversation_history}
            AVAILABLE PRODUCTS: {available_products}

            Create specific, helpful recommendations that:
            1. Match their stated needs
            2. Fit their apparent budget/preferences
            3. Provide clear benefits
            4. Sound natural and conversational

            Format as 3 separate recommendations.
            """)

            chain = recommendation_prompt | self.llm | self.str_parser
            
            recommendations = await chain.ainvoke({
                "customer_profile": customer_profile,
                "conversation_history": conversation_history,
                "available_products": str(available_products[:5])  # Limit for context
            })

            return recommendations.split('\n')[:3]

        except Exception as e:
            self.logger.error(f"Error generating recommendations: {e}")
            return ["I'd recommend checking out our bestselling products that match your needs."]

# Global instance
enhanced_response_generator = EnhancedResponseGenerator()
