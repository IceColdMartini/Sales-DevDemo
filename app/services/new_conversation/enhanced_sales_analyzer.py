"""
Enhanced Sales Funnel Analyzer
==============================

Improved            "PURCHASE_CONFIRMATION": [
                r"\b(yes,?\\s*i'll take it|i'll buy it|let me buy|proceed with)\b",
                r"\b(how do i buy|help me purchase|complete the order)\b",
                r"\b(finalize|confirm purchase|ready to order)\b",
                r"\b(let's do this|i'm convinced|take my money)\b"
            ], stage analysis with better accuracy and consistency.
Addresses the stage detection inconsistencies identified in testing.
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
import re

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
    """Enhanced sales analysis output."""
    current_stage: str = Field(description="Current sales stage")
    is_ready_to_buy: bool = Field(description="Whether customer is ready to buy")
    confidence_score: float = Field(description="Confidence in the analysis (0-1)")
    reasoning: str = Field(description="Reasoning for the analysis")
    next_steps: List[str] = Field(description="Recommended next steps")
    stage_progression: bool = Field(description="Whether stage progressed from previous")
    customer_sentiment: str = Field(description="Customer emotional state")

class EnhancedSalesFunnelAnalyzer:
    """
    Enhanced sales funnel analyzer with improved accuracy and consistency.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Stage transition patterns - more comprehensive matching
        self.stage_patterns = {
            "INITIAL_INTEREST": [
                r"\b(hi|hello|hey|looking for|need|want|help|interested)\b",
                r"\b(upgrade|improve|find|recommend|suggest)\b",
                r"\b(routine|products|skincare|beauty|makeup|hair)\b"
            ],
            "PRODUCT_DISCOVERY": [
                r"\b(tell me|what|features|benefits|ingredients|recommend|compare)\b",
                r"\b(options|choices|alternatives|types|kinds)\b",
                r"\b(best for|suitable|right for|good for)\b",
                r"\b(clean|natural|organic|sulfate-free|paraben-free)\b",
                r"\b(do you have|carry|sell|stock|brand|brands)\b"
            ],
            "PRICE_EVALUATION": [
                r"\b(how much does|what's the price|price range|cost|budget)\b",
                r"\b(under \$|over \$|within|affordable|expensive)\b",
                r"\b(discount|sale|deal|offer|promotion|cheaper)\b",
                r"\b(worth it|value for money|reasonable price)\b"
            ],
            "PURCHASE_INTENT": [
                r"\b(I'd like to get|I want to get|I want the|interested in buying|thinking of getting)\b",
                r"\b(that looks perfect|sounds great|I like that|looks good)\b",
                r"\b(I'll take the|let me get the|I need that|I'll get)\b",
                r"\b(ready to buy|want to purchase|I'll go with)\b"
            ],
            "PURCHASE_CONFIRMATION": [
                r"\b(I'll take it|yes|confirm|proceed|finalize)\b",
                r"\b(complete|purchase|order|buy it|take it)\b",
                r"\b(how do I buy|help me complete|let's do this)\b",
                r"\b(convinced|trust|ready|perfect)\b"
            ]
        }

        # Purchase readiness indicators - more nuanced
        self.readiness_patterns = {
            "high_readiness": [
                r"\b(I'll take|I want to buy|ready to purchase|let me get)\b",
                r"\b(how do I|help me buy|complete order|proceed)\b",
                r"\b(perfect|convinced|trust|let's do this)\b"
            ],
            "moderate_readiness": [
                r"\b(interested in|thinking of|considering|might)\b",
                r"\b(sounds good|looks great|seems perfect)\b",
                r"\b(I'd like|I think|probably)\b"
            ],
            "low_readiness": [
                r"\b(not sure|worried|concerned|hesitant)\b",
                r"\b(still thinking|need time|maybe later)\b",
                r"\b(what if|but|however|although)\b"
            ]
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
                temperature=0.2,  # Lower temperature for more consistent analysis
                max_tokens=300
            )
        else:
            self.llm = None

        # Enhanced sales analysis prompt
        self.sales_prompt = ChatPromptTemplate.from_template("""
        You are an expert sales psychologist analyzing customer behavior. Your goal is to accurately determine the customer's sales stage and purchase readiness.

        ENHANCED STAGE DEFINITIONS:
        
        INITIAL_INTEREST:
        - General greetings and broad needs ("Hi, I need skincare products")
        - Early exploration without specific product focus
        - Keywords: hi, hello, looking for, need, want, help, interested

        PRODUCT_DISCOVERY:
        - Asking about specific products, features, or ingredients
        - Comparing options or seeking recommendations
        - Keywords: tell me about, what is, features, benefits, recommend, compare, best for

        PRICE_EVALUATION:
        - Questions about pricing, budget constraints, or value
        - Seeking deals, discounts, or cost information
        - Keywords: price, cost, expensive, budget, afford, how much, worth, value

        PURCHASE_INTENT:
        - Expressing interest in specific products ("I'd like to get...")
        - Showing clear preference or inclination to buy
        - Keywords: I think, I'd like, I want, interested in getting, I'll take, ready to

        PURCHASE_CONFIRMATION:
        - Clear commitment to buy ("I'll take it", "Yes, let's do this")
        - Asking about purchase process or completion
        - Keywords: I'll take it, yes, confirm, proceed, complete, buy it, how do I buy

        PURCHASE READINESS ANALYSIS:
        - HIGH: Customer uses definitive language ("I'll take", "let me buy", "how do I purchase")
        - MODERATE: Customer shows strong interest ("sounds perfect", "I'd like to get")  
        - LOW: Customer is still exploring or has concerns ("not sure", "worried", "still thinking")

        ANALYSIS CONTEXT:
        Previous Stage: {previous_stage}
        Current Message: "{current_message}"
        Conversation History: {conversation_history}
        Products Discussed: {products}

        CRITICAL ANALYSIS RULES:
        1. Focus primarily on the customer's LATEST message for stage determination
        2. Consider conversation flow - stages should generally progress forward
        3. Purchase readiness should align with definitive customer language
        4. If customer uses purchase language ("I'll take", "let me buy") → ALWAYS set ready=True
        5. Be consistent - similar messages should produce similar results
        6. Consider emotional indicators (excitement, hesitation, confidence)

        Provide your analysis with high confidence and clear reasoning.

        {format_instructions}
        """)

        self.sales_parser = PydanticOutputParser(pydantic_object=SalesAnalysis)

    async def analyze_conversation(self,
                                 conversation_history: List[BaseMessage],
                                 matched_products: List[Any],
                                 previous_stage: str,
                                 current_message: str) -> SalesAnalysis:
        """
        Enhanced conversation analysis with improved accuracy.
        """
        try:
            # First, try rule-based analysis for speed and consistency
            rule_based_analysis = self._rule_based_analysis(current_message, previous_stage)
            
            if rule_based_analysis and rule_based_analysis.confidence_score >= 0.8:
                self.logger.info(f"🎯 High-confidence rule-based analysis: {rule_based_analysis.current_stage}")
                return rule_based_analysis

            # Fall back to LLM analysis for complex cases
            if self.llm:
                llm_analysis = await self._llm_analysis(
                    conversation_history, matched_products, previous_stage, current_message
                )
                
                # Combine rule-based and LLM insights
                final_analysis = self._combine_analyses(rule_based_analysis, llm_analysis)
                return final_analysis
            else:
                # Use rule-based as fallback
                return rule_based_analysis or self._fallback_analysis(current_message, previous_stage)

        except Exception as e:
            self.logger.error(f"❌ Enhanced analysis failed: {e}")
            return self._fallback_analysis(current_message, previous_stage)

    def _rule_based_analysis(self, message: str, previous_stage: str) -> Optional[SalesAnalysis]:
        """
        Fast, consistent rule-based analysis using pattern matching.
        """
        message_lower = message.lower()
        
        # Special handling for first message (no previous stage or INITIAL_INTEREST)
        if not previous_stage or previous_stage == "INITIAL_INTEREST":
            # Check if it's clearly a first-time inquiry
            first_time_patterns = [
                r"\b(hi|hello|hey|looking for|need|want|help)\b",
                r"\b(i'm looking|i need|i want|can you help)\b"
            ]
            for pattern in first_time_patterns:
                if re.search(pattern, message_lower):
                    return SalesAnalysis(
                        current_stage="INITIAL_INTEREST",
                        is_ready_to_buy=False,
                        confidence_score=0.9,
                        reasoning="First-time inquiry detected",
                        next_steps=["Ask about specific needs", "Recommend products"],
                        stage_progression=True,
                        customer_sentiment="curious"
                    )
        
        # Calculate pattern scores for each stage
        stage_scores = {}
        for stage, patterns in self.stage_patterns.items():
            score = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, message_lower))
                score += matches
            stage_scores[stage] = score

        # Determine stage with highest score
        if not any(stage_scores.values()):
            # If no patterns match, infer from context and previous stage
            return self._contextual_stage_inference(message_lower, previous_stage)
            
        predicted_stage = max(stage_scores, key=stage_scores.get)
        confidence = min(stage_scores[predicted_stage] / len(self.stage_patterns[predicted_stage]), 1.0)

        # Boost confidence for patterns we've specifically improved
        improved_patterns = {
            "PURCHASE_INTENT": [r"\b(I'd like to get|I want to get)\b"],
            "PRODUCT_DISCOVERY": [r"\b(do you have|carry|brands?)\b"],
            "INITIAL_INTEREST": [r"\b(i need|i want.*under|looking for)\b"]
        }
        
        for stage, patterns in improved_patterns.items():
            if stage == predicted_stage:
                for pattern in patterns:
                    if re.search(pattern, message_lower):
                        confidence = min(confidence + 0.3, 1.0)  # Boost confidence
                        break

        # Apply stage progression logic - don't skip stages inappropriately
        stage_order = ["INITIAL_INTEREST", "PRODUCT_DISCOVERY", "PRICE_EVALUATION", "PURCHASE_INTENT", "PURCHASE_CONFIRMATION"]
        current_index = stage_order.index(predicted_stage) if predicted_stage in stage_order else 0
        previous_index = stage_order.index(previous_stage) if previous_stage in stage_order else 0
        
        # Don't jump more than 2 stages ahead unless it's clearly purchase confirmation
        if current_index - previous_index > 2 and predicted_stage != "PURCHASE_CONFIRMATION":
            # Check for explicit purchase confirmation language
            purchase_confirm_patterns = [r"\b(i'll take it|yes\s*,?\s*i'll buy|how do i buy|let me purchase)\b"]
            is_purchase_confirm = any(re.search(pattern, message_lower) for pattern in purchase_confirm_patterns)
            
            if not is_purchase_confirm:
                # Step down to a more reasonable progression
                predicted_stage = stage_order[min(previous_index + 1, len(stage_order) - 1)]
                confidence *= 0.8  # Reduce confidence for adjusted prediction

        # Determine purchase readiness
        readiness_score = 0
        for readiness_type, patterns in self.readiness_patterns.items():
            for pattern in patterns:
                matches = len(re.findall(pattern, message_lower))
                if readiness_type == "high_readiness":
                    readiness_score += matches * 3
                elif readiness_type == "moderate_readiness":
                    readiness_score += matches * 2
                else:  # low_readiness
                    readiness_score -= matches

        is_ready = readiness_score >= 2

        # Stage progression logic
        stage_order = ["INITIAL_INTEREST", "PRODUCT_DISCOVERY", "PRICE_EVALUATION", "PURCHASE_INTENT", "PURCHASE_CONFIRMATION"]
        previous_index = stage_order.index(previous_stage) if previous_stage in stage_order else 0
        current_index = stage_order.index(predicted_stage)
        progressed = current_index > previous_index

        # Reasoning
        reasoning = f"Rule-based analysis: '{message[:50]}...' matches {predicted_stage} patterns with {confidence:.2f} confidence. "
        reasoning += f"Readiness score: {readiness_score}, Ready: {is_ready}"

        return SalesAnalysis(
            current_stage=predicted_stage,
            is_ready_to_buy=is_ready,
            confidence_score=confidence,
            reasoning=reasoning,
            next_steps=self._generate_next_steps(predicted_stage, is_ready),
            stage_progression=progressed,
            customer_sentiment=self._analyze_sentiment(message_lower)
        )

    def _contextual_stage_inference(self, message_lower: str, previous_stage: str) -> Optional[SalesAnalysis]:
        """
        Infer stage from context when no patterns match.
        """
        # Check for purchase intent language more carefully
        purchase_intent_signals = [
            r"\b(i'd like|i'll take|that.*perfect|sounds good|looks great)\b"
        ]
        
        purchase_confirm_signals = [
            r"\b(yes,?\\s*i'll take it|how do i buy|let me buy|proceed with)\b"
        ]
        
        # Check for purchase confirmation first (more specific)
        for pattern in purchase_confirm_signals:
            if re.search(pattern, message_lower):
                return SalesAnalysis(
                    current_stage="PURCHASE_CONFIRMATION",
                    is_ready_to_buy=True,
                    confidence_score=0.8,
                    reasoning="Contextual analysis: Purchase confirmation language detected",
                    next_steps=["Process order", "Provide payment options"],
                    stage_progression=True,
                    customer_sentiment="excited"
                )
        
        # Check for purchase intent (less specific)
        for pattern in purchase_intent_signals:
            if re.search(pattern, message_lower):
                return SalesAnalysis(
                    current_stage="PURCHASE_INTENT",
                    is_ready_to_buy=False,
                    confidence_score=0.7,
                    reasoning="Contextual analysis: Purchase interest detected",
                    next_steps=["Confirm product details", "Discuss purchase process"],
                    stage_progression=True,
                    customer_sentiment="interested"
                )
        
        # Default progression based on previous stage
        stage_order = ["INITIAL_INTEREST", "PRODUCT_DISCOVERY", "PRICE_EVALUATION", "PURCHASE_INTENT", "PURCHASE_CONFIRMATION"]
        if previous_stage in stage_order:
            current_index = stage_order.index(previous_stage)
            next_stage = stage_order[min(current_index + 1, len(stage_order) - 1)]
            
            return SalesAnalysis(
                current_stage=next_stage,
                is_ready_to_buy=False,
                confidence_score=0.5,
                reasoning=f"Contextual progression from {previous_stage}",
                next_steps=self._generate_next_steps(next_stage, False),
                stage_progression=True,
                customer_sentiment="neutral"
            )
        
        return None

    async def _llm_analysis(self, conversation_history, matched_products, previous_stage, current_message):
        """
        LLM-based analysis for complex cases.
        """
        try:
            formatted_conversation = self._format_conversation(conversation_history)
            formatted_products = self._format_products(matched_products)

            chain = self.sales_prompt | self.llm | self.sales_parser
            
            analysis = await chain.ainvoke({
                "conversation_history": formatted_conversation,
                "products": formatted_products,
                "previous_stage": previous_stage,
                "current_message": current_message,
                "format_instructions": self.sales_parser.get_format_instructions()
            })

            self.logger.info(f"🤖 LLM Analysis: {analysis.current_stage}, Ready={analysis.is_ready_to_buy}")
            return analysis

        except Exception as e:
            self.logger.error(f"❌ LLM analysis failed: {e}")
            return None

    def _combine_analyses(self, rule_based: Optional[SalesAnalysis], llm_based: Optional[SalesAnalysis]) -> SalesAnalysis:
        """
        Combine rule-based and LLM analyses for best results.
        """
        if not rule_based and not llm_based:
            return self._fallback_analysis("", "INITIAL_INTEREST")
        
        if not rule_based:
            return llm_based
        if not llm_based:
            return rule_based

        # Prefer rule-based for specific patterns we've trained it on
        specific_patterns = ["purchase_intent", "product_discovery", "initial_interest"]
        rule_stage_lower = rule_based.current_stage.lower()
        
        # Check if rule-based detected a specific pattern we trust
        if any(pattern in rule_based.reasoning.lower() for pattern in ["purchase", "brand", "discovery"]):
            if rule_based.confidence_score >= 0.6:  # Lower threshold for specific patterns
                self.logger.info(f"🎯 Using rule-based for specific pattern: {rule_based.current_stage}")
                return rule_based
        
        # Original logic for high confidence rule-based
        if rule_based.confidence_score >= 0.8:
            return rule_based
        
        # For ambiguous cases, prefer rule-based if it has reasonable confidence
        if rule_based.confidence_score >= 0.5 and llm_based.confidence_score < 0.9:
            # Use rule-based stage but combine readiness logic
            combined = rule_based
            if llm_based.confidence_score > rule_based.confidence_score:
                combined.is_ready_to_buy = llm_based.is_ready_to_buy
            return combined
        else:
            # Use LLM but with rule-based readiness if it's more confident
            combined = llm_based
            if rule_based.confidence_score > llm_based.confidence_score:
                combined.is_ready_to_buy = rule_based.is_ready_to_buy
            return combined

    def _analyze_sentiment(self, message: str) -> str:
        """
        Analyze customer sentiment from message.
        """
        positive_words = ["great", "perfect", "love", "excellent", "amazing", "wonderful"]
        negative_words = ["worried", "concerned", "unsure", "hesitant", "doubt", "problem"]
        
        positive_count = sum(1 for word in positive_words if word in message)
        negative_count = sum(1 for word in negative_words if word in message)
        
        if positive_count > negative_count:
            return "positive"
        elif negative_count > positive_count:
            return "negative"
        else:
            return "neutral"

    def _generate_next_steps(self, stage: str, is_ready: bool) -> List[str]:
        """
        Generate contextual next steps based on stage and readiness.
        """
        if stage == "INITIAL_INTEREST":
            return ["Ask about specific needs", "Recommend relevant products", "Understand skin/hair type"]
        elif stage == "PRODUCT_DISCOVERY":
            return ["Provide detailed product information", "Discuss ingredients and benefits", "Compare options"]
        elif stage == "PRICE_EVALUATION":
            return ["Share pricing information", "Highlight value proposition", "Mention any deals"]
        elif stage == "PURCHASE_INTENT":
            return ["Confirm product selection", "Address any concerns", "Guide toward purchase"]
        elif stage == "PURCHASE_CONFIRMATION":
            return ["Assist with checkout process", "Provide order details", "Confirm purchase"]
        else:
            return ["Engage customer", "Understand needs", "Build rapport"]

    def _fallback_analysis(self, message: str, previous_stage: str) -> SalesAnalysis:
        """
        Simple fallback analysis when other methods fail.
        """
        # Basic keyword detection
        message_lower = message.lower()
        
        if any(word in message_lower for word in ["buy", "purchase", "take", "order", "complete"]):
            stage = "PURCHASE_CONFIRMATION"
            ready = True
        elif any(word in message_lower for word in ["price", "cost", "budget", "expensive", "cheap"]):
            stage = "PRICE_EVALUATION"
            ready = False
        elif any(word in message_lower for word in ["tell me", "what", "feature", "benefit", "ingredient"]):
            stage = "PRODUCT_DISCOVERY"
            ready = False
        else:
            stage = "INITIAL_INTEREST"
            ready = False

        return SalesAnalysis(
            current_stage=stage,
            is_ready_to_buy=ready,
            confidence_score=0.6,
            reasoning="Fallback analysis based on basic keyword detection",
            next_steps=self._generate_next_steps(stage, ready),
            stage_progression=True,
            customer_sentiment="neutral"
        )

    def _format_conversation(self, conversation_history: List[BaseMessage]) -> str:
        """Format conversation history for analysis."""
        if not conversation_history:
            return "No conversation history"
        
        # Get last 5 messages for context
        recent = conversation_history[-5:]
        formatted = []
        
        for msg in recent:
            if hasattr(msg, 'type') and hasattr(msg, 'content'):
                role = "Customer" if msg.type == "human" else "Assistant"
                formatted.append(f"{role}: {msg.content[:100]}...")
        
        return "\n".join(formatted)

    def _format_products(self, matched_products: List[Any]) -> str:
        """Format products for analysis."""
        if not matched_products:
            return "No products discussed"
        
        products = []
        for i, match in enumerate(matched_products[:3]):
            product = match.product
            products.append(f"{i+1}. {product.get('name', 'Product')} - {product.get('brand', 'Brand')}")
        
        return "\n".join(products)

    def should_handover_to_agent(self, analysis: SalesAnalysis, conversation_length: int) -> bool:
        """
        Enhanced handover decision logic.
        """
        # Handover conditions
        if analysis.current_stage == "PURCHASE_CONFIRMATION" and analysis.is_ready_to_buy:
            return True
        if conversation_length >= 8:  # Long conversation
            return True
        if analysis.customer_sentiment == "negative" and conversation_length >= 4:
            return True
        
        return False

# Create enhanced analyzer instance
enhanced_sales_analyzer = EnhancedSalesFunnelAnalyzer()
