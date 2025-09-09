"""
Sales Funnel Analyzer
=====================

Analyzes conversation to determine sales stage and purchase readiness.
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import BaseMessage
try:
    from langchain_core.output_parsers import PydanticOutputParser
except ImportError:
    from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class SalesStage(Enum):
    """Sales funnel stages."""
    INITIAL_INTEREST = "INITIAL_INTEREST"
    PRODUCT_DISCOVERY = "PRODUCT_DISCOVERY"
    PRICE_EVALUATION = "PRICE_EVALUATION"
    PURCHASE_INTENT = "PURCHASE_INTENT"
    PURCHASE_CONFIRMATION = "PURCHASE_CONFIRMATION"

class SalesAnalysis(BaseModel):
    """Pydantic model for sales analysis output."""
    current_stage: str = Field(description="Current sales stage")
    is_ready_to_buy: bool = Field(description="Whether customer is ready to buy")
    confidence_score: float = Field(description="Confidence in the analysis (0-1)")
    reasoning: str = Field(description="Reasoning for the analysis")
    next_steps: List[str] = Field(description="Recommended next steps")

class SalesFunnelAnalyzer:
    """
    Analyzes conversation to determine sales stage and purchase readiness.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

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
                temperature=0.2,
                max_tokens=800
            )
        else:
            self.llm = None

        # Sales analysis prompt
        self.sales_analysis_prompt = ChatPromptTemplate.from_template("""
        You are an expert sales analyst. Analyze the conversation to determine the EXACT sales stage.

        SALES STAGE CRITERIA (BE PRECISE):

        INITIAL_INTEREST:
        - Customer just started conversation
        - General questions like "hi", "hello", "looking for", "need", "want"
        - No specific products mentioned yet
        - Early stage, first 1-2 messages
        - Examples: "Hi, I'm looking for skincare products", "I need some moisturizer"

        PRODUCT_DISCOVERY:
        - Customer asking about specific products or features
        - Questions like "tell me about", "what is", "features", "benefits", "ingredients"
        - Showing interest in learning more about products
        - Examples: "Tell me about this serum", "What are the benefits?"

        PRICE_EVALUATION:
        - Customer asking about prices, costs, budget
        - Questions like "how much", "price", "cost", "expensive", "cheap", "afford"
        - Comparing options or concerned about budget
        - Examples: "How much does this cost?", "Is this within my budget?"

        PURCHASE_INTENT:
        - Customer shows clear intent to buy
        - Statements like "I want to buy", "I'll take it", "ready to purchase"
        - Asking about purchase process, shipping, payment
        - Examples: "I want to buy this product", "Let me purchase it"

        PURCHASE_CONFIRMATION:
        - Customer confirming they want to proceed with purchase
        - Statements like "yes, confirm", "proceed", "finalize", "complete purchase"
        - Ready to finish the transaction
        - Examples: "Yes, I want to buy it", "Confirm my order"

        PURCHASE READINESS:
        - True if customer shows clear intent to buy NOW or SOON
        - True if they say "I want to buy", "Let me purchase", "Yes, I'll take it"
        - True if they ask to complete purchase or need help with checkout
        - True if they express desire to buy specific products
        - False only if they're still researching or have strong objections
        - Be realistic - most customers saying "I want to buy" are ready

        CRITICAL ANALYSIS RULES (FOLLOW THESE EXACTLY):
        1. ANALYZE THE CUSTOMER'S LATEST MESSAGE ONLY - IGNORE CONVERSATION HISTORY
        2. MATCH KEYWORDS TO DETERMINE STAGE:
           - "hi", "hello", "looking for", "need", "want" → INITIAL_INTEREST
           - "tell me about", "what is", "features", "benefits", "recommend" → PRODUCT_DISCOVERY
           - "how much", "price", "cost", "expensive", "budget", "afford" → PRICE_EVALUATION
           - "I want to buy", "I'll take", "ready to purchase", "interested in" → PURCHASE_INTENT, is_ready_to_buy=True
           - "yes", "confirm", "proceed", "finalize", "complete purchase" → PURCHASE_CONFIRMATION, is_ready_to_buy=True
        3. IF MESSAGE CONTAINS PURCHASE WORDS → SET is_ready_to_buy=True
        4. NEVER STAY IN SAME STAGE - ALWAYS PROGRESS IF MESSAGE SHOWS ADVANCEMENT

        SPECIFIC MESSAGE ANALYSIS:
        - "I need something for anti-aging and vitamin C serum" → PRODUCT_DISCOVERY (specific products)
        - "How much do these products cost?" → PRICE_EVALUATION (price questions)
        - "The Vitamin C Serum sounds really good. I'm also interested in..." → PURCHASE_INTENT (shows interest in buying)
        - "Yes, I want to buy both products. Please help me complete the purchase" → PURCHASE_CONFIRMATION, is_ready_to_buy=True

        KEYWORD PRIORITY (HIGHEST TO LOWEST):
        1. Purchase confirmation: "yes", "confirm", "proceed", "finalize", "complete purchase" → PURCHASE_CONFIRMATION, Ready=True
        2. Purchase intent: "I want to buy", "I'll take", "ready to purchase", "interested in buying" → PURCHASE_INTENT, Ready=True
        3. Price questions: "how much", "price", "cost", "budget", "afford" → PRICE_EVALUATION
        4. Product questions: "tell me about", "what is", "features", "benefits", "recommend" → PRODUCT_DISCOVERY
        5. General interest: "hi", "hello", "looking for", "need", "want" → INITIAL_INTEREST

        Current customer message: "{current_message}"

        Previous stage: {previous_stage}

        {format_instructions}
        """)

        self.sales_parser = PydanticOutputParser(pydantic_object=SalesAnalysis)

    async def analyze_conversation(self, conversation_history: List[BaseMessage],
                                 matched_products: List[Any],
                                 previous_stage: str = "INITIAL_INTEREST",
                                 current_message: str = "") -> SalesAnalysis:
        """
        Analyze the conversation to determine sales stage and readiness.

        Args:
            conversation_history: List of conversation messages
            matched_products: List of matched products
            previous_stage: Previous sales stage
            current_message: Current user message for immediate analysis

        Returns:
            SalesAnalysis: Analysis results
        """
        try:
            # Format conversation for prompt
            conversation_text = self._format_conversation(conversation_history)

            # Format products for prompt
            products_text = self._format_products(matched_products)

            # Create analysis chain
            if self.llm:
                chain = self.sales_analysis_prompt | self.llm | self.sales_parser
            else:
                # Fallback without LLM
                chain = self.sales_analysis_prompt | self.sales_parser

            # Run analysis
            if self.llm:
                result = await chain.ainvoke({
                    "current_message": current_message if current_message else conversation_text.split('\n')[-1] if conversation_text else "",
                    "previous_stage": previous_stage,
                    "format_instructions": self.sales_parser.get_format_instructions()
                })
                self.logger.info(f"🤖 LLM Analysis: {result}")
            else:
                # Fallback mode
                self.logger.info("⚠️ Using fallback analysis (no LLM available)")
                result = self._fallback_analysis(conversation_history, previous_stage, current_message)

            self.logger.info(f"📊 Sales analysis: Stage={result.current_stage}, Ready={result.is_ready_to_buy}")
            return result

        except Exception as e:
            self.logger.error(f"Error analyzing conversation: {e}")
            # Return fallback analysis with current message
            return self._fallback_analysis(conversation_history, previous_stage, current_message)

    def _format_conversation(self, conversation_history: List[BaseMessage]) -> str:
        """
        Format conversation history for analysis.

        Args:
            conversation_history: List of conversation messages

        Returns:
            str: Formatted conversation text
        """
        formatted_lines = []

        # Ensure conversation_history is a list
        if not isinstance(conversation_history, list):
            return "No conversation history available"

        # Get last 10 messages safely
        recent_messages = conversation_history[-10:] if len(conversation_history) > 0 else conversation_history

        for msg in recent_messages:
            if hasattr(msg, 'type') and hasattr(msg, 'content'):
                role = "Customer" if msg.type == "human" else "Assistant"
                formatted_lines.append(f"{role}: {msg.content}")
            else:
                # Handle other message types
                formatted_lines.append(f"Message: {str(msg)}")

        return "\n".join(formatted_lines)

    def _format_products(self, matched_products: List[Any]) -> str:
        """
        Format matched products for analysis.

        Args:
            matched_products: List of matched products

        Returns:
            str: Formatted products text
        """
        if not matched_products:
            return "No products matched yet"

        product_lines = []
        for i, product_match in enumerate(matched_products[:3]):  # Top 3 products
            product = product_match.product
            confidence = product_match.confidence_score

            product_lines.append(
                f"{i+1}. {product.get('name', 'Unknown')} "
                f"(Confidence: {confidence:.2f}) - "
                f"${product.get('price', 0):.2f}"
            )

        return "\n".join(product_lines)

    def _fallback_analysis(self, conversation_history: List[BaseMessage],
                          previous_stage: str, current_message: str = "") -> SalesAnalysis:
        """
        Fallback analysis using rule-based approach.

        Args:
            conversation_history: List of conversation messages
            previous_stage: Previous sales stage
            current_message: Current user message

        Returns:
            SalesAnalysis: Basic analysis results
        """
        # Ensure conversation_history is a list
        if not isinstance(conversation_history, list):
            conversation_history = []

        # Get the last few messages plus current message safely
        recent_messages = conversation_history[-5:] if len(conversation_history) > 0 else []
        conversation_text = " ".join([msg.content for msg in recent_messages if hasattr(msg, 'content')])

        # Add current message if provided
        if current_message:
            conversation_text += " " + current_message

        current_stage = previous_stage
        is_ready = False
        confidence = 0.5
        reasoning_parts = []
        next_steps = []

        # Rule-based stage detection
        lower_text = conversation_text.lower()

        # Initial interest indicators - check this first for new conversations
        initial_keywords = ['hi', 'hello', 'looking for', 'need', 'want', 'searching', 'interested in', 'skincare', 'products']
        if len(conversation_history) <= 2:  # Early in conversation
            if any(keyword in lower_text for keyword in initial_keywords):
                current_stage = "INITIAL_INTEREST"
                confidence = 0.8
                reasoning_parts.append("Customer is initiating contact and showing initial interest")
                next_steps.append("Provide product recommendations and information")

        # Confirmation indicators - check this early
        confirm_keywords = ['yes', 'confirm', 'proceed', 'go ahead', 'finalize', 'ready now', 'let\'s do it', 'complete the purchase']
        if any(keyword in lower_text for keyword in confirm_keywords):
            current_stage = "PURCHASE_CONFIRMATION"
            is_ready = True
            confidence = 0.9
            reasoning_parts.append("Customer is confirming purchase")
            next_steps.append("Complete the purchase transaction")

        # Purchase intent indicators - expanded list
        purchase_keywords = [
            'buy', 'purchase', 'order', 'get it', 'want to buy', 'ready to buy',
            'i want', 'i\'ll take', 'i\'m interested in buying', 'let me buy',
            'i think i want', 'i\'m ready to', 'yes i want', 'confirm purchase'
        ]
        if any(keyword in lower_text for keyword in purchase_keywords):
            current_stage = "PURCHASE_INTENT"
            is_ready = True
            confidence = 0.8
            reasoning_parts.append("Customer expressed clear purchase intent")
            next_steps.append("Guide customer through purchase process")

        # Price inquiry indicators
        price_keywords = ['price', 'cost', 'how much', 'expensive', 'cheap', 'afford', 'budget']
        if any(keyword in lower_text for keyword in price_keywords) and not is_ready:
            current_stage = "PRICE_EVALUATION"
            confidence = 0.7
            reasoning_parts.append("Customer is asking about pricing")
            next_steps.append("Provide pricing information and options")

        # Product discovery indicators
        discovery_keywords = ['tell me about', 'what is', 'features', 'benefits', 'ingredients', 'how does it work']
        if any(keyword in lower_text for keyword in discovery_keywords) and current_stage == "INITIAL_INTEREST":
            current_stage = "PRODUCT_DISCOVERY"
            confidence = 0.6
            reasoning_parts.append("Customer is exploring product details")
            next_steps.append("Provide detailed product information")

        # Build reasoning
        reasoning = "; ".join(reasoning_parts) if reasoning_parts else "General conversation analysis"

        # Default next steps if none specified
        if not next_steps:
            next_steps = ["Continue the conversation", "Ask clarifying questions"]

        return SalesAnalysis(
            current_stage=current_stage,
            is_ready_to_buy=is_ready,
            confidence_score=confidence,
            reasoning=reasoning,
            next_steps=next_steps
        )

    def should_handover_to_agent(self, analysis: SalesAnalysis,
                               conversation_length: int) -> bool:
        """
        Determine if conversation should be handed over to human agent.

        Args:
            analysis: Sales analysis results
            conversation_length: Number of messages in conversation

        Returns:
            bool: Whether to handover
        """
        # Handover conditions
        if analysis.is_ready_to_buy:
            return True

        if analysis.current_stage == "PURCHASE_CONFIRMATION":
            return True

        if conversation_length > 15:  # Long conversation
            return True

        if analysis.confidence_score < 0.3:  # Low confidence in analysis
            return True

        return False
