#!/usr/bin/env python3
"""
Fixes for the Sales Agent Conversation and Handover Issues

This file contains fixes for the issues identified in the comprehensive test:
1. Product ID extraction problems
2. Premature is_ready=True triggers
3. Multiple product tracking issues
4. LangChain integration recommendations
"""

import json
from typing import List, Dict, Any, Tuple
import logging

class SalesAgentFixes:
    """Collection of fixes for the sales agent system"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def create_enhanced_conversation_service(self):
        """Create an enhanced conversation service with better product tracking"""
        return """
# Enhanced Conversation Service with fixes
from app.db.mongo_handler import mongo_handler
from app.db.postgres_handler import postgres_handler
from app.services.ai_service import ai_service
from app.models.schemas import Message
from typing import List, Dict
import logging
import re

class EnhancedConversationService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def process_message(self, message: Message):
        # 1. Get conversation history (limit to last 10 conversations)
        conversation_data = mongo_handler.get_conversation(message.sender)
        full_conversation = conversation_data['conversation'] if conversation_data else []
        
        # Keep only last 10 exchanges (20 messages: 10 user + 10 assistant)
        conversation_history = full_conversation[-20:] if len(full_conversation) > 20 else full_conversation
        
        # Check if this is first interaction
        is_first_interaction = len(full_conversation) == 0

        # 2. Extract keywords using enhanced LLM with business context
        self.logger.info(f"Extracting keywords from: {message.text}")
        keywords = await ai_service.extract_keywords_with_llm(message.text)
        self.logger.info(f"Extracted keywords: {keywords}")

        # 3. Get all products (can be optimized with pagination for millions of products)
        all_products = postgres_handler.get_all_products()
        
        # 4. NEW: Analyze sales stage for better product filtering and business logic
        conversation_history_str = self._format_conversation_history(conversation_history)
        initial_product_info = self._build_product_info(all_products[:10])  # Sample for analysis
        
        sales_analysis = ai_service.analyze_sales_stage(
            conversation_history=conversation_history_str,
            user_message=message.text,
            product_info=initial_product_info
        )
        
        self.logger.info(f"Sales Analysis: {sales_analysis}")
        
        # 5. Find relevant products using LLM-based similarity matching
        # Only try to match products if we have relevant keywords
        relevant_products_with_scores = []
        if keywords:  # Only proceed if keywords were found
            self.logger.info(f"Matching {len(keywords)} keywords against {len(all_products)} products")
            relevant_products_with_scores = ai_service.find_matching_products_with_llm(keywords, all_products)
            
            # Log matching results
            for product, score in relevant_products_with_scores:
                self.logger.info(f"Matched: {product['name']} (Score: {score:.1f}%)")
        else:
            self.logger.info("No relevant keywords extracted - conversation may be off-topic")
        
        # Extract just the products for response generation
        relevant_products = [product for product, score in relevant_products_with_scores]
        
        # 6. ENHANCED: Apply price range filtering if customer mentioned budget constraints
        price_range = sales_analysis.get('price_range_mentioned')
        if price_range and relevant_products:
            self.logger.info(f"Filtering products by price range: {price_range}")
            relevant_products = ai_service.filter_products_by_price_range(relevant_products, price_range)
            self.logger.info(f"After price filtering: {len(relevant_products)} products remain")
        
        # 7. ENHANCED: Merge with conversation context products for better tracking
        context_products = self._extract_products_from_conversation_context(conversation_history, all_products)
        if context_products:
            self.logger.info(f"Found {len(context_products)} products from conversation context")
            # Merge context products with current relevant products, avoiding duplicates
            merged_products = self._merge_product_lists(relevant_products, context_products)
            relevant_products = merged_products
        
        # 8. Build product information for AI (may be empty for off-topic conversations)
        product_info = self._build_product_info(relevant_products)

        # 9. FIXED: Generate response using enhanced sales funnel with proper is_ready handling
        response_text, is_ready = ai_service.generate_response(
            conversation_history=conversation_history_str,
            product_info=product_info,
            user_message=message.text,
            is_first_interaction=is_first_interaction
        )

        # 10. Save updated conversation
        updated_conversation = full_conversation + [
            {"role": "user", "content": message.text},
            {"role": "assistant", "content": response_text}
        ]
        mongo_handler.save_conversation(message.sender, updated_conversation)

        # 11. ENHANCED: Determine most interested product(s) with better multiple product handling
        product_interested = self._determine_interested_product_enhanced(relevant_products, keywords, sales_analysis, is_ready)
        
        # 12. FIXED: Extract product IDs with better matching algorithm
        interested_product_ids = self._extract_product_ids_enhanced(relevant_products, sales_analysis, product_interested, all_products)

        return {
            "sender": message.sender,
            "product_interested": product_interested,  # Product names for display
            "interested_product_ids": interested_product_ids,  # Product IDs for Routing Agent
            "response_text": response_text,
            "is_ready": is_ready,
        }

    def _extract_products_from_conversation_context(self, conversation: List[Dict], all_products: List[Dict]) -> List[Dict]:
        \"\"\"Extract products mentioned in conversation history for better context tracking\"\"\"
        context_products = []
        
        # Look for product names mentioned in the conversation
        for message in conversation:
            content = message.get('content', '').lower()
            
            # Find products mentioned by name or brand
            for product in all_products:
                product_name = product['name'].lower()
                product_words = product_name.split()
                
                # Check if product name or significant words appear in conversation
                if (product_name in content or 
                    any(word in content for word in product_words if len(word) > 3)):
                    
                    if product not in context_products:
                        context_products.append(product)
        
        return context_products[:5]  # Limit to 5 most relevant
    
    def _merge_product_lists(self, current_products: List[Dict], context_products: List[Dict]) -> List[Dict]:
        \"\"\"Merge current products with context products, avoiding duplicates\"\"\"
        merged = current_products.copy()
        current_ids = {p['id'] for p in current_products}
        
        for product in context_products:
            if product['id'] not in current_ids:
                merged.append(product)
        
        return merged

    def _extract_product_ids_enhanced(self, relevant_products: List[Dict], sales_analysis: Dict, 
                                     product_interested: str, all_products: List[Dict]) -> List[str]:
        \"\"\"ENHANCED: Extract product IDs with better matching algorithm\"\"\"
        if not product_interested:
            return []
        
        interested_product_ids = []
        
        # Get products from sales analysis first
        interested_products_from_analysis = sales_analysis.get('interested_products', [])
        
        # Parse product names to find
        product_names_to_find = []
        
        if interested_products_from_analysis:
            product_names_to_find.extend(interested_products_from_analysis)
        
        if product_interested and product_interested != "None":
            if "Multiple products:" in product_interested:
                # Parse multiple products format: "Multiple products: Product1, Product2" 
                products_str = product_interested.replace("Multiple products: ", "")
                product_names_to_find.extend([p.strip() for p in products_str.split(",")])
            else:
                product_names_to_find.append(product_interested)
        
        # ENHANCED MATCHING: Multiple strategies for finding product IDs
        for product_name in product_names_to_find:
            found_id = self._find_product_id_by_name(product_name, relevant_products, all_products)
            if found_id and found_id not in interested_product_ids:
                interested_product_ids.append(found_id)
        
        self.logger.info(f"Product ID extraction: {len(product_names_to_find)} names -> {len(interested_product_ids)} IDs")
        return interested_product_ids

    def _find_product_id_by_name(self, product_name: str, relevant_products: List[Dict], 
                                all_products: List[Dict]) -> str:
        \"\"\"Find product ID using multiple matching strategies\"\"\"
        product_name_lower = product_name.lower().strip()
        
        # Strategy 1: Exact name match in relevant products
        for product in relevant_products:
            if product_name_lower == product['name'].lower():
                return product.get('id')
        
        # Strategy 2: Partial name match in relevant products
        for product in relevant_products:
            if product_name_lower in product['name'].lower() or product['name'].lower() in product_name_lower:
                return product.get('id')
        
        # Strategy 3: Brand/keyword match in relevant products
        product_keywords = product_name_lower.split()
        for product in relevant_products:
            product_name_words = product['name'].lower().split()
            if any(keyword in product_name_words for keyword in product_keywords if len(keyword) > 2):
                return product.get('id')
        
        # Strategy 4: Search in all products as fallback
        for product in all_products:
            if (product_name_lower in product['name'].lower() or 
                product['name'].lower() in product_name_lower):
                return product.get('id')
        
        self.logger.warning(f"Could not find product ID for: {product_name}")
        return None

    def _format_conversation_history(self, conversation: List[Dict]) -> str:
        \"\"\"Format conversation history for AI context\"\"\"
        if not conversation:
            return "No previous conversation."
        
        formatted = []
        for msg in conversation:
            role = "Customer" if msg['role'] == 'user' else "Assistant"
            formatted.append(f"{role}: {msg['content']}")
        
        return "\\n".join(formatted)

    def _build_product_info(self, products: List[Dict]) -> str:
        \"\"\"Build detailed product information for AI response generation\"\"\"
        if not products:
            return \"\"\"We have a comprehensive collection of premium beauty and personal care products including:
            
            - Premium Beauty Soaps & Body Care (moisturizing bars, luxury fragrances, traditional ingredients)
            - Professional Hair Care Solutions (anti-hair fall shampoos, organic treatments, strengthening formulas)
            - Nourishing Hair Oils & Styling Products (coconut oils, ayurvedic amla preparations, herbal treatments)
            - Captivating Fragrances & Perfumes (body sprays, premium woody perfumes, traditional attars)
            - Advanced Skincare Solutions (fairness creams, gentle herbal face washes, ayurvedic treatments)
            - Specialized Grooming Essentials (antibacterial protection, natural extracts)
            
            Featured brands include Lux, Dove, Pantene, Head & Shoulders, Garnier, AXE, Fogg, Wild Stone, and local favorites like Keya Seth and Tibbet.
            
            What specific beauty or personal care needs can I help you with today?\"\"\"
        
        product_details = []
        for product in products:
            price_info = f"৳{product['price']}"
            if product.get('sale_price'):
                price_info = f"৳{product['sale_price']} (was ৳{product['price']})"
            
            tags = product.get('product_tag', [])
            tag_str = f" - Tags: {', '.join(tags[:5])}" if tags else ""
            
            details = f"**{product['name']}** - {price_info}\\n"
            details += f"   Rating: {product.get('rating', 0):.1f} stars | Stock: {product.get('stock_count', 0)} units"
            details += tag_str
            
            product_details.append(details.strip())
        
        return "\\n\\n".join(product_details)

    def _determine_interested_product_enhanced(self, relevant_products: List[Dict], keywords: List[str], 
                                             sales_analysis: Dict, is_ready: bool = False) -> str:
        \"\"\"ENHANCED: Determine product interest with better multiple product handling\"\"\"
        
        # PRIORITY 1: If customer is ready to buy, prioritize products from sales analysis
        if is_ready:
            interested_products_from_analysis = sales_analysis.get('interested_products', [])
            if interested_products_from_analysis:
                # For purchase confirmation, return the products they specifically mentioned
                if len(interested_products_from_analysis) == 1:
                    return interested_products_from_analysis[0]
                else:
                    return f"Multiple products: {', '.join(interested_products_from_analysis)}"
        
        # PRIORITY 2: Check if sales analysis provided specific product interest (normal flow)
        interested_products_from_analysis = sales_analysis.get('interested_products', [])
        if interested_products_from_analysis and relevant_products:
            # Match analysis products with our product catalog
            matching_products = []
            for analysis_product in interested_products_from_analysis:
                for product in relevant_products:
                    if (analysis_product.lower() in product['name'].lower() or
                        any(word in product['name'].lower() for word in analysis_product.lower().split() if len(word) > 2)):
                        matching_products.append(product['name'])
                        break
            
            if matching_products:
                if len(matching_products) == 1:
                    return matching_products[0]
                else:
                    return f"Multiple products: {', '.join(matching_products)}"
        
        # PRIORITY 3: Return products from sales analysis even if not in catalog (for purchase confirmations)
        if interested_products_from_analysis:
            if len(interested_products_from_analysis) == 1:
                return interested_products_from_analysis[0]
            else:
                return f"Multiple products: {', '.join(interested_products_from_analysis)}"
        
        # PRIORITY 4: Fallback to relevant products
        if not relevant_products:
            return None
            
        return self._determine_interested_product_fallback(relevant_products, keywords)

    def _determine_interested_product_fallback(self, relevant_products: List[Dict], keywords: List[str]) -> str:
        \"\"\"Fallback method for determining product interest\"\"\"
        if not relevant_products:
            return None
        
        # Handle multiple products case
        if len(relevant_products) > 3:
            # If customer is interested in many products, return the top 3 as a summary
            top_products = relevant_products[:3]
            product_names = [p['name'] for p in top_products]
            return f"Multiple products: {', '.join(product_names)}"
        elif len(relevant_products) > 1:
            # For 2-3 products, list them all
            product_names = [p['name'] for p in relevant_products]
            return f"Multiple products: {', '.join(product_names)}"
        else:
            # Single product case
            return relevant_products[0]['name']

# Create the enhanced service instance
enhanced_conversation_service = EnhancedConversationService()
"""

    def create_ai_service_fixes(self):
        """Create fixes for the AI service is_ready logic"""
        return """
# AI Service Fixes for is_ready flag management

class AIServiceFixes:
    
    def fix_purchase_intent_response(self):
        \"\"\"Fix the purchase intent response to NOT set is_ready=True\"\"\"
        return '''
    def _generate_purchase_intent_response(self, user_message: str, product_info: str, sales_analysis: Dict) -> Tuple[str, bool]:
        \"\"\"FIXED: Handle when customer shows purchase intent but hasn't confirmed yet - ASK FOR EXPLICIT CONFIRMATION\"\"\"
        interested_products = sales_analysis.get('interested_products', [])
        price_range = sales_analysis.get('price_range_mentioned')
        customer_saw_prices = sales_analysis.get('customer_saw_prices', False)
        
        system_prompt = f\"\"\"You are Zara, a beauty consultant sensing strong purchase intent. The customer is interested but hasn't explicitly confirmed purchase yet.

        PURCHASE INTENT CONFIRMATION APPROACH:
        1. Acknowledge their strong interest enthusiastically
        2. Confirm exactly which product(s) they're interested in
        3. Provide a clear final price summary for their choice(s)
        4. Ask for EXPLICIT confirmation: "Would you like to proceed with this purchase?" or "Shall I help you order this?"
        5. Make it easy for them to say "yes" with clear next steps
        6. Be encouraging but not pushy
        7. Handle multiple products by summarizing all choices with total

        CRITICAL: Ask for explicit purchase confirmation. Don't assume - make them say "yes" to buying.

        CONFIRMATION PHRASES TO USE:
        - "Would you like to proceed with purchasing [product]?"
        - "Shall I help you place an order for this?"
        - "Are you ready to purchase [product] for ৳[price]?"
        - "Would you like to go ahead and buy this?"

        BUSINESS CONTEXT: {self.business_context}
        
        CUSTOMER INTEREST: {interested_products if interested_products else 'Products discussed'}
        CUSTOMER SAW PRICES: {customer_saw_prices}
        BUDGET RANGE: {price_range if price_range else 'Not specified'}\"\"\"

        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f\"\"\"Customer said: "{user_message}"
                
                Products they're interested in: {product_info}
                
                They're showing purchase intent! Confirm their exact choice with pricing and ask for explicit purchase confirmation. Make it clear and easy for them to say yes to buying.\"\"\"
            }
        ]

        # FIXED: Should NOT be ready yet - customer hasn't explicitly confirmed
        return self._make_api_call(messages, temperature=0.6, max_tokens=200, is_ready=False)
        '''
    
    def fix_sales_stage_analysis(self):
        \"\"\"Fix the sales stage analysis for better is_ready detection\"\"\"
        return '''
    def analyze_sales_stage_enhanced(self, conversation_history: str, user_message: str, product_info: str = "") -> Dict:
        \"\"\"ENHANCED: Advanced sales funnel analysis with stricter is_ready control\"\"\"
        
        # First, run the original analysis
        analysis = self.analyze_sales_stage(conversation_history, user_message, product_info)
        
        # ENHANCED RULE ENFORCEMENT: Stricter control over is_ready flag
        
        # Rule 1: Explicit purchase confirmation phrases
        explicit_purchase_phrases = [
            "yes, i want to buy", "i'll take", "i'll buy", "i want to purchase",
            "i want both", "i'll purchase", "yes, i want both", "i want to order",
            "let me buy", "i'll take both", "i want the", "i'll get"
        ]
        
        user_message_lower = user_message.lower().strip()
        
        # Check for explicit purchase confirmation
        has_explicit_purchase = any(phrase in user_message_lower for phrase in explicit_purchase_phrases)
        
        # Rule 2: NOT purchase confirmation phrases (should be FALSE)
        non_purchase_phrases = [
            "sounds good", "looks good", "i like this", "this is perfect", 
            "seems perfect", "tell me more", "what's the price", "how much",
            "i'm interested", "looks interesting", "perfect for me"
        ]
        
        has_non_purchase = any(phrase in user_message_lower for phrase in non_purchase_phrases)
        
        # Rule 3: Purchase intent phrases (showing interest but not confirming)
        purchase_intent_phrases = [
            "perfect, i want", "great, i want", "i think i want", "i'd like"
        ]
        
        has_purchase_intent = any(phrase in user_message_lower for phrase in purchase_intent_phrases)
        
        # ENHANCED LOGIC: Override LLM decision with strict rules
        if has_explicit_purchase and not has_non_purchase:
            print(f"🎯 EXPLICIT PURCHASE DETECTED: {user_message}")
            analysis["current_stage"] = "PURCHASE_CONFIRMATION"
            analysis["is_ready_to_buy"] = True
            analysis["explicit_purchase_words"] = True
            analysis["customer_saw_prices"] = True  # Assume prices were discussed
            analysis["prices_shown_in_conversation"] = True
        elif has_purchase_intent and not has_explicit_purchase:
            print(f"🔥 PURCHASE INTENT DETECTED: {user_message}")
            analysis["current_stage"] = "PURCHASE_INTENT"
            analysis["is_ready_to_buy"] = False  # NOT ready until explicit confirmation
            analysis["next_action"] = "ask_for_confirmation"
        elif has_non_purchase:
            print(f"❌ NON-PURCHASE PHRASE DETECTED: {user_message}")
            analysis["is_ready_to_buy"] = False
            if analysis["current_stage"] == "PURCHASE_CONFIRMATION":
                analysis["current_stage"] = "PURCHASE_INTENT"
        
        # Final validation: is_ready should only be True for PURCHASE_CONFIRMATION
        if analysis["current_stage"] != "PURCHASE_CONFIRMATION":
            analysis["is_ready_to_buy"] = False
        
        print(f"🔍 ENHANCED ANALYSIS: Stage={analysis['current_stage']}, Ready={analysis['is_ready_to_buy']}")
        
        return analysis
        '''

# Apply the fixes
ai_service_fixes = AIServiceFixes()
"""

    def create_langchain_enhanced_service(self):
        """Create a LangChain-enhanced version of the conversation service"""
        return """
# LangChain Enhanced Conversation Service
# This demonstrates how LangChain could improve the current system

from langchain.memory import ConversationBufferWindowMemory, ConversationEntityMemory
from langchain.schema import BaseMemory
from langchain.prompts import ChatPromptTemplate
from langchain.schema.runnable import RunnablePassthrough
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import json

class SalesAnalysis(BaseModel):
    \"\"\"Structured output for sales analysis\"\"\"
    current_stage: str = Field(description="Current sales stage")
    is_ready_to_buy: bool = Field(description="Whether customer is ready to purchase")
    interested_products: List[str] = Field(description="Products customer is interested in")
    confidence_level: float = Field(description="Confidence in the analysis")
    next_action: str = Field(description="Recommended next action")

class ProductStateMemory(BaseMemory):
    \"\"\"Custom memory for tracking product state across conversation\"\"\"
    
    def __init__(self):
        self.products_mentioned = []
        self.products_interested = []
        self.products_removed = []
        self.prices_shown = {}
        
    def save_context(self, inputs: Dict[str, Any], outputs: Dict[str, str]) -> None:
        # Track products mentioned in conversation
        user_message = inputs.get("user_message", "")
        agent_response = outputs.get("response", "")
        
        # Extract and save product mentions
        # Implementation would extract products from text
        pass
        
    def clear(self) -> None:
        self.products_mentioned = []
        self.products_interested = []
        self.products_removed = []
        self.prices_shown = {}
    
    @property
    def memory_variables(self) -> List[str]:
        return ["product_state"]
    
    def load_memory_variables(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "product_state": {
                "mentioned": self.products_mentioned,
                "interested": self.products_interested,
                "removed": self.products_removed,
                "prices_shown": self.prices_shown
            }
        }

class LangChainEnhancedConversationService:
    \"\"\"LangChain-enhanced conversation service with better state management\"\"\"
    
    def __init__(self):
        # Initialize memory components
        self.conversation_memory = ConversationBufferWindowMemory(
            k=10,  # Keep last 10 exchanges
            return_messages=True,
            memory_key="chat_history"
        )
        
        self.entity_memory = ConversationEntityMemory(
            llm=None,  # Would use actual LLM instance
            memory_key="entities"
        )
        
        self.product_memory = ProductStateMemory()
        
        # Initialize output parser
        self.sales_parser = PydanticOutputParser(pydantic_object=SalesAnalysis)
        
        # Sales stage analysis prompt
        self.sales_analysis_prompt = ChatPromptTemplate.from_messages([
            ("system", \"\"\"You are an expert sales consultant. Analyze the customer's journey stage.
            
            SALES STAGES:
            1. INITIAL_INTEREST - Just expressed interest
            2. NEED_CLARIFICATION - Gathering requirements  
            3. PRODUCT_DISCOVERY - Learning about products
            4. PRICE_EVALUATION - Evaluating pricing
            5. CONSIDERATION - Weighing options
            6. OBJECTION_HANDLING - Addressing concerns
            7. PURCHASE_INTENT - Strong buying signals
            8. PURCHASE_CONFIRMATION - Explicit confirmation
            
            RULES:
            - is_ready_to_buy=true ONLY for explicit purchase confirmation
            - Customer must see prices before purchase confirmation
            - Track all products mentioned for multiple product scenarios
            
            {format_instructions}
            \"\"\"),
            ("human", \"\"\"
            Conversation History: {chat_history}
            Current Message: {user_message}
            Product Context: {product_context}
            Current Product State: {product_state}
            
            Analyze the customer's sales stage and provide structured output.
            \"\"\")
        ])
        
        # Response generation prompt
        self.response_prompt = ChatPromptTemplate.from_messages([
            ("system", \"\"\"You are Zara, a friendly beauty consultant.
            
            Based on the sales analysis, generate an appropriate response.
            
            Current Stage: {current_stage}
            Customer Intent: {customer_intent}
            Products Interested: {interested_products}
            Next Action: {next_action}
            
            RESPONSE GUIDELINES:
            - For PURCHASE_INTENT: Ask for explicit confirmation
            - For PURCHASE_CONFIRMATION: Confirm purchase and prepare handover
            - Always be natural and helpful
            - Include prices when showing products
            \"\"\"),
            ("human", \"{user_message}\")
        ])
        
    async def process_message_enhanced(self, message: Message) -> Dict:
        \"\"\"Process message with LangChain enhanced flow\"\"\"
        
        # Load conversation context
        chat_history = self.conversation_memory.load_memory_variables({})["chat_history"]
        entities = self.entity_memory.load_memory_variables({})["entities"]
        product_state = self.product_memory.load_memory_variables({})["product_state"]
        
        # Get products from database
        all_products = postgres_handler.get_all_products()
        product_context = self._build_product_context(all_products)
        
        # Analyze sales stage with structured output
        sales_analysis_chain = (
            RunnablePassthrough.assign(
                format_instructions=lambda _: self.sales_parser.get_format_instructions()
            )
            | self.sales_analysis_prompt
            | llm  # Would use actual LLM instance
            | self.sales_parser
        )
        
        sales_analysis = sales_analysis_chain.invoke({
            "user_message": message.text,
            "chat_history": chat_history,
            "product_context": product_context,
            "product_state": product_state
        })
        
        # Generate response based on analysis
        response_chain = (
            self.response_prompt
            | llm  # Would use actual LLM instance
        )
        
        response_text = response_chain.invoke({
            "user_message": message.text,
            "current_stage": sales_analysis.current_stage,
            "customer_intent": "purchase" if sales_analysis.is_ready_to_buy else "inquiry",
            "interested_products": sales_analysis.interested_products,
            "next_action": sales_analysis.next_action
        })
        
        # Save to memory
        self.conversation_memory.save_context(
            {"input": message.text},
            {"output": response_text}
        )
        
        self.entity_memory.save_context(
            {"input": message.text},
            {"output": response_text}
        )
        
        self.product_memory.save_context(
            {"user_message": message.text},
            {"response": response_text}
        )
        
        # Extract product IDs (enhanced with vector similarity)
        interested_product_ids = self._extract_product_ids_vector_search(
            sales_analysis.interested_products, 
            all_products
        )
        
        return {
            "sender": message.sender,
            "product_interested": ", ".join(sales_analysis.interested_products) if sales_analysis.interested_products else None,
            "interested_product_ids": interested_product_ids,
            "response_text": response_text,
            "is_ready": sales_analysis.is_ready_to_buy,
        }
    
    def _extract_product_ids_vector_search(self, product_names: List[str], all_products: List[Dict]) -> List[str]:
        \"\"\"Extract product IDs using vector similarity search\"\"\"
        # This would use embeddings to find the most similar products
        # For now, using simple string matching as fallback
        product_ids = []
        
        for product_name in product_names:
            for product in all_products:
                if product_name.lower() in product['name'].lower():
                    product_ids.append(product['id'])
                    break
        
        return product_ids
    
    def _build_product_context(self, products: List[Dict]) -> str:
        \"\"\"Build product context for prompts\"\"\"
        context = []
        for product in products[:20]:  # Limit for token efficiency
            context.append(f"{product['name']}: ৳{product['price']} - {', '.join(product.get('product_tag', [])[:3])}")
        return "\\n".join(context)

# Benefits of LangChain Integration:
# 1. Structured conversation memory management
# 2. Entity tracking for products across conversations
# 3. Structured output parsing for consistent responses
# 4. Template-based prompt management
# 5. Chain composition for complex workflows
# 6. Better state management for multi-turn conversations
# 7. Vector search capabilities for product matching
"""

    def generate_implementation_plan(self):
        """Generate a comprehensive implementation plan"""
        return """
# COMPREHENSIVE IMPLEMENTATION PLAN FOR SALES AGENT IMPROVEMENTS

## Phase 1: Immediate Fixes (Week 1)

### 1.1 Fix Product ID Extraction
- ✅ Enhance `_extract_product_ids_enhanced` method
- ✅ Add multiple matching strategies (exact, partial, keyword)
- ✅ Add fallback to search all products
- ✅ Add detailed logging for debugging

### 1.2 Fix is_ready Flag Management
- ✅ Fix `_generate_purchase_intent_response` to return `is_ready=False`
- ✅ Add stricter explicit purchase phrase detection
- ✅ Enhance sales stage analysis with better rule enforcement
- ✅ Add debug logging for is_ready decisions

### 1.3 Improve Multiple Product Tracking
- ✅ Add conversation context product extraction
- ✅ Merge current and context products
- ✅ Better product name parsing for multiple products
- ✅ Enhanced product interest determination

## Phase 2: System Enhancements (Week 2-3)

### 2.1 Enhanced Conversation Service
- Replace current conversation_service with enhanced version
- Add product context tracking across conversations
- Improve error handling and logging
- Add conversation state persistence

### 2.2 Sales Funnel Improvements
- Add stricter stage transition rules
- Implement mandatory price introduction workflow
- Add customer budget tracking and filtering
- Improve objection handling responses

### 2.3 Testing and Validation
- Run comprehensive test suite
- Validate all scenarios pass
- Performance testing with multiple concurrent users
- Load testing with large product catalogs

## Phase 3: LangChain Integration (Week 4-6)

### 3.1 Memory Management
- Implement ConversationBufferWindowMemory
- Add ConversationEntityMemory for product tracking
- Create custom ProductStateMemory
- Add conversation summarization

### 3.2 Structured Workflows
- Implement StateGraph for sales funnel
- Add conditional transitions between stages
- Create tool integration for database operations
- Add structured output parsing

### 3.3 Vector Database Integration
- Implement product embeddings
- Add semantic search for product matching
- Create vector database for fast retrieval
- Add similarity-based product recommendations

## Phase 4: Advanced Features (Week 7-8)

### 4.1 Advanced AI Capabilities
- Add ReAct agents for complex reasoning
- Implement Chain-of-Thought for decision making
- Add multi-step product recommendation
- Create personalized customer experiences

### 4.2 Analytics and Monitoring
- Add conversation analytics
- Track conversion rates by stage
- Monitor is_ready flag accuracy
- Add A/B testing for different approaches

### 4.3 Performance Optimization
- Optimize database queries
- Add caching for frequent operations
- Implement batch processing for products
- Add response time monitoring

## Expected Improvements

### Before LangChain:
- Manual prompt engineering
- Basic conversation tracking
- Simple product matching
- Limited state management

### After LangChain:
- Structured conversation flows
- Advanced memory management
- Vector-based product search
- Intelligent state transitions
- Better error handling
- Scalable architecture

## Success Metrics

### Functional Metrics:
- is_ready flag accuracy: >95%
- Product ID extraction success: >90%
- Multiple product handling: >85%
- Response quality score: >4.0/5.0

### Performance Metrics:
- Response time: <2 seconds
- Concurrent users: >100
- Database query efficiency: <100ms
- Memory usage optimization: <500MB

### Business Metrics:
- Conversation completion rate: >80%
- Customer satisfaction: >4.2/5.0
- Conversion to purchase: >25%
- Average conversation length: 5-7 exchanges

## Implementation Timeline

Week 1: Immediate fixes and testing
Week 2: Enhanced conversation service
Week 3: Sales funnel improvements
Week 4: LangChain memory integration
Week 5: Structured workflows
Week 6: Vector database setup
Week 7: Advanced AI features
Week 8: Analytics and optimization

## Resource Requirements

### Development:
- 1 Senior Python Developer
- 1 AI/ML Engineer
- 1 Database Engineer
- 1 QA Engineer

### Infrastructure:
- Vector database (Pinecone/Weaviate)
- Enhanced Azure OpenAI quota
- MongoDB optimization
- PostgreSQL performance tuning

### Budget Estimate:
- Development: $50,000-$75,000
- Infrastructure: $5,000-$10,000/month
- Testing and QA: $15,000-$20,000
- Total: $70,000-$105,000
"""

if __name__ == "__main__":
    fixes = SalesAgentFixes()
    
    print("=== SALES AGENT FIXES AND ENHANCEMENTS ===\\n")
    
    print("1. Enhanced Conversation Service:")
    print(fixes.create_enhanced_conversation_service()[:500] + "...\\n")
    
    print("2. AI Service Fixes:")
    print(fixes.create_ai_service_fixes()[:500] + "...\\n")
    
    print("3. LangChain Enhancement:")
    print(fixes.create_langchain_enhanced_service()[:500] + "...\\n")
    
    print("4. Implementation Plan:")
    print(fixes.generate_implementation_plan()[:500] + "...")
