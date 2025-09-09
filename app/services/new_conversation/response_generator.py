"""
Response Generator
==================

Generates human-like responses using LangChain with advanced prompt engineering.
"""

import logging
from typing import List, Dict, Any, Optional
import json

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
try:
    from langchain_core.output_parsers import PydanticOutputParser
except ImportError:
    from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

from app.core.config import Settings
from . import ConversationResponse

# Import the enhanced response generator
try:
    from app.services.enhanced_response_generator import enhanced_response_generator
    ENHANCED_GENERATOR_AVAILABLE = True
except ImportError:
    ENHANCED_GENERATOR_AVAILABLE = False
    enhanced_response_generator = None

logger = logging.getLogger(__name__)

class ResponseContent(BaseModel):
    """Pydantic model for response content."""
    message: str = Field(description="The response message to send to customer")
    tone: str = Field(description="Tone of the response (friendly, professional, enthusiastic, etc.)")
    persuasion_level: str = Field(description="Level of persuasion (low, medium, high)")
    call_to_action: Optional[str] = Field(description="Specific call to action if applicable")

class ResponseGenerator:
    """
    Generates human-like responses using advanced prompt engineering.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.config = Settings()

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
                temperature=0.7,
                max_tokens=1200
            )
        else:
            self.llm = None

        # Main response generation prompt
        self.response_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert beauty consultant and sales professional. Your goal is to provide helpful, engaging, and persuasive responses while maintaining a natural, human-like conversation flow.

Key Guidelines:
- Be conversational and friendly, like talking to a friend
- Show genuine enthusiasm for beauty products and customer needs
- Provide specific product recommendations with reasons
- Address customer concerns directly and empathetically
- Use persuasive language naturally, not pushy
- Ask relevant follow-up questions to continue engagement
- Keep responses concise but informative (2-4 sentences typically)
- End with a clear call-to-action when appropriate

IMPORTANT: If the user message contains "[SYSTEM: Customer is ready for handover to human agent]", you MUST include handover messaging in your response. This means:
- Acknowledge that you're connecting them to a human specialist
- Explain that a representative will help complete their purchase
- Include phrases like "transferring you", "connecting you", or "next available representative"
- Keep the tone professional and reassuring

Current Sales Context:
- Sales Stage: {sales_stage}
- Customer Readiness: {readiness}
- Matched Products: {products}

Remember: Your responses should feel natural and helpful, not like a sales script."""),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{user_message}"),
            ("assistant", "Based on the conversation and product matches, craft a response that:")
        ])

        # Response refinement prompt for quality control
        self.refinement_prompt = ChatPromptTemplate.from_template("""
        Review and refine this response to ensure it's optimal:

        Original Response: {response}

        Sales Context:
        - Stage: {sales_stage}
        - Readiness: {readiness}
        - Products: {products}

        Refinement Criteria:
        1. Natural conversation flow
        2. Appropriate persuasion level
        3. Clear value proposition
        4. Engaging call-to-action
        5. Professional yet friendly tone

        Provide the refined response:
        """)

    async def generate_response(self, user_message: str,
                              conversation_history: List[BaseMessage],
                              matched_products: List[Any],
                              sales_analysis: Any,
                              sender_id: str,
                              should_handover: bool = False) -> ConversationResponse:
        """
        Generate a response based on user input and context using enhanced AI techniques.

        Args:
            user_message: Current user message
            conversation_history: Previous conversation messages
            matched_products: Matched products from product matcher
            sales_analysis: Sales analysis results
            sender_id: Unique sender identifier
            should_handover: Whether to prepare for handover to human agent

        Returns:
            ConversationResponse: Generated response with metadata
        """
        try:
            # Format products for prompt
            products_context = self._format_products_context(matched_products)
            
            # Format conversation history
            conversation_str = self._format_conversation_history(conversation_history)

            # Determine if this is the first interaction
            is_first_interaction = len(conversation_history) == 0

            # Handle handover scenario
            final_user_message = user_message
            if should_handover:
                final_user_message = f"{user_message}\n\n[SYSTEM: Customer is ready for handover to human agent. Include handover messaging in response.]"

            # Use enhanced response generator if available
            if ENHANCED_GENERATOR_AVAILABLE and enhanced_response_generator:
                self.logger.info("🚀 Using enhanced response generator with advanced AI techniques")
                
                enhanced_result = await enhanced_response_generator.generate_enhanced_response(
                    conversation_history=conversation_str,
                    user_message=final_user_message,
                    product_info=products_context,
                    sales_stage=sales_analysis.current_stage,
                    is_first_interaction=is_first_interaction
                )
                
                response_text = enhanced_result["response_text"]
                confidence = enhanced_result["confidence_level"]
                
                self.logger.info(f"✨ Enhanced response quality score: {enhanced_result.get('quality_score', 'N/A')}/10")
                if enhanced_result.get("was_refined", False):
                    self.logger.info("🔧 Response was refined for better quality")
                
            else:
                # Fallback to original method
                self.logger.info("⚡ Using standard response generator")
                
                prompt_vars = {
                    "sales_stage": sales_analysis.current_stage,
                    "readiness": "Ready to buy" if sales_analysis.is_ready_to_buy else "Still exploring",
                    "products": products_context,
                    "user_message": final_user_message,
                    "chat_history": conversation_history[-10:]
                }
                
                initial_response = await self._generate_initial_response(prompt_vars)
                refined_response = await self._refine_response(initial_response, prompt_vars)
                response_text = refined_response.message
                confidence = sales_analysis.confidence_score

            # Create response object
            response = ConversationResponse(
                sender=sender_id,
                response_text=response_text,
                product_interested=self._extract_interested_products(matched_products),
                interested_product_ids=[p.product.get('id') for p in matched_products if p.product.get('id')],
                is_ready=sales_analysis.is_ready_to_buy,
                sales_stage=sales_analysis.current_stage,
                confidence=confidence
            )

            self.logger.info(f"💬 Generated response for {sender_id}: {len(response_text)} chars, confidence: {confidence:.2f}")
            return response

        except Exception as e:
            self.logger.error(f"Error generating response: {e}")
            # Return fallback response
            return self._generate_fallback_response(user_message, sender_id, sales_analysis.is_ready_to_buy)

    async def _generate_initial_response(self, prompt_vars: Dict[str, Any]) -> ResponseContent:
        """
        Generate initial response using LangChain.

        Args:
            prompt_vars: Variables for the prompt

        Returns:
            ResponseContent: Generated response content
        """
        try:
            # Create the chain
            if self.llm:
                chain = self.response_prompt | self.llm
            else:
                chain = self.response_prompt

            # Generate response
            if self.llm:
                response_text = await chain.ainvoke(prompt_vars)
                # Extract the actual message content
                if hasattr(response_text, 'content'):
                    message_content = response_text.content
                else:
                    message_content = str(response_text)
            else:
                # Fallback without LLM
                message_content = self._create_response_text(prompt_vars)

            # Return structured response
            return ResponseContent(
                message=message_content,
                tone="friendly",
                persuasion_level="medium",
                call_to_action="Ask about preferences"
            )

        except Exception as e:
            self.logger.error(f"Error in initial response generation: {e}")
            return ResponseContent(
                message="I'd be happy to help you find the perfect beauty products!",
                tone="friendly",
                persuasion_level="low"
            )

    def _create_response_text(self, prompt_vars: Dict[str, Any]) -> str:
        """
        Create response text based on context.

        Args:
            prompt_vars: Prompt variables

        Returns:
            str: Generated response text
        """
        user_message = prompt_vars.get("user_message", "").lower()
        sales_stage = prompt_vars.get("sales_stage", "INITIAL_INTEREST")
        products = prompt_vars.get("products", "")

        # Basic response logic based on stage and user input
        if sales_stage == "INITIAL_INTEREST":
            if "lipstick" in user_message:
                return "I'd love to help you find the perfect lipstick! We have amazing options in various shades. What skin tone are you looking for, and do you prefer matte or glossy finish?"
            elif "skincare" in user_message:
                return "Great choice focusing on skincare! Healthy skin is the foundation of beautiful makeup. Are you looking for moisturizers, serums, or cleansers?"
            else:
                return "Hi! I'm here to help you discover amazing beauty products. What are you interested in today - makeup, skincare, or hair care?"

        elif sales_stage == "PRODUCT_DISCOVERY":
            return f"Based on what you've told me, I think you'd love our {products}. These products are perfect for your needs. Would you like me to tell you more about the benefits and how to use them?"

        elif sales_stage == "PRICE_EVALUATION":
            return "I understand you want to make sure you're getting the best value. Our products are priced competitively and we often have great promotions. Let me check current pricing for you."

        elif sales_stage == "PURCHASE_INTENT":
            return "Excellent! It sounds like you're ready to make a purchase. I can help you complete this quickly and easily. Shall we proceed with your order?"

        elif sales_stage == "PURCHASE_CONFIRMATION":
            return "Perfect! Let's get everything set up for you. I'll need just a few details to complete your purchase. Are you ready to proceed?"

        else:
            return "I'm here to help you with all your beauty needs! What can I assist you with today?"

    async def _refine_response(self, initial_response: ResponseContent,
                             prompt_vars: Dict[str, Any]) -> ResponseContent:
        """
        Refine the response for better quality.

        Args:
            initial_response: Initial response content
            prompt_vars: Prompt variables

        Returns:
            ResponseContent: Refined response content
        """
        try:
            # Create refinement chain
            if self.llm:
                refinement_chain = self.refinement_prompt | self.llm

                # Refine the response
                refined_text = await refinement_chain.ainvoke({
                    "response": initial_response.message,
                    "sales_stage": prompt_vars.get("sales_stage", "UNKNOWN"),
                    "readiness": prompt_vars.get("readiness", "UNKNOWN"),
                    "products": prompt_vars.get("products", "No products"),
                    "user_message": prompt_vars.get("user_message", "")
                })

                # Extract the refined message
                if hasattr(refined_text, 'content'):
                    refined_message = refined_text.content
                else:
                    refined_message = str(refined_text)

                # Return refined response
                return ResponseContent(
                    message=refined_message,
                    tone=initial_response.tone,
                    persuasion_level=initial_response.persuasion_level,
                    call_to_action=initial_response.call_to_action
                )
            else:
                # Return original response if no LLM available
                return initial_response

        except Exception as e:
            self.logger.error(f"Error refining response: {e}")
            return initial_response

    def _format_products_context(self, matched_products: List[Any]) -> str:
        """
        Format matched products for context.

        Args:
            matched_products: List of matched products

        Returns:
            str: Formatted products context
        """
        if not matched_products:
            return "No specific products matched yet"

        product_lines = []
        for i, product_match in enumerate(matched_products[:3]):  # Top 3
            product = product_match.product
            confidence = product_match.confidence_score

            product_lines.append(
                f"- {product.get('name', 'Unknown Product')} "
                f"(Match: {confidence:.1%}) - "
                f"${product.get('price', 0):.2f}"
            )

        return "\n".join(product_lines)

    def _extract_interested_products(self, matched_products: List[Any]) -> List[str]:
        """
        Extract product names that the customer is interested in.

        Args:
            matched_products: List of matched products

        Returns:
            List[str]: List of interested product names
        """
        if not matched_products:
            return []

        return [product_match.product.get('name', 'Unknown')
                for product_match in matched_products[:3]]

    def _format_conversation_history(self, conversation_history: List[BaseMessage]) -> str:
        """
        Format conversation history as a string for the enhanced generator.
        
        Args:
            conversation_history: List of conversation messages
            
        Returns:
            str: Formatted conversation history
        """
        if not conversation_history:
            return "This is the start of the conversation."
            
        formatted_messages = []
        for message in conversation_history[-10:]:  # Last 10 messages
            if isinstance(message, HumanMessage):
                formatted_messages.append(f"Customer: {message.content}")
            elif isinstance(message, AIMessage):
                formatted_messages.append(f"Assistant: {message.content}")
            else:
                # Handle other message types
                role = getattr(message, 'role', 'unknown')
                content = getattr(message, 'content', str(message))
                formatted_messages.append(f"{role.capitalize()}: {content}")
                
        return "\n".join(formatted_messages)

    def _generate_fallback_response(self, user_message: str, sender_id: str,
                                  is_ready: bool) -> ConversationResponse:
        """
        Generate a fallback response when main generation fails.

        Args:
            user_message: User's message
            sender_id: Sender identifier
            is_ready: Whether customer is ready to buy

        Returns:
            ConversationResponse: Fallback response
        """
        return ConversationResponse(
            sender=sender_id,
            response_text="I'd be happy to help you with beauty products! Could you tell me more about what you're looking for?",
            product_interested=[],
            interested_product_ids=[],
            is_ready=is_ready,
            sales_stage="INITIAL_INTEREST",
            confidence=0.5
        )

    def _generate_handover_message(self, sales_analysis: Any, matched_products: List[Any]) -> str:
        """
        Generate a handover message for when customer should be transferred to human agent.

        Args:
            sales_analysis: Sales analysis results
            matched_products: Matched products

        Returns:
            str: Handover message
        """
        if sales_analysis.is_ready_to_buy:
            message = "I can see you're ready to make a purchase! Let me connect you with one of our beauty specialists who can help you complete your order and answer any final questions."
        elif sales_analysis.current_stage == "PURCHASE_CONFIRMATION":
            message = "You're at the point of confirming your purchase! I'll transfer you to our sales team who can finalize everything for you."
        else:
            message = "I'd like to connect you with one of our beauty experts who can provide more personalized assistance."

        # Add product context if available
        if matched_products:
            product_names = []
            for product in matched_products[:3]:  # Show up to 3 products
                if hasattr(product, 'product') and product.product and product.product.get('name'):
                    product_names.append(product.product['name'])

            if product_names:
                message += f" They'll be able to help you with {', '.join(product_names)} and any other products you're interested in."

        message += "\n\nPlease hold for just a moment while I transfer you to the next available representative."

        return message
