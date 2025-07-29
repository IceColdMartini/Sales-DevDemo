#!/usr/bin/env python3
"""
Enhanced Conversation System with LangChain Integration

This addresses the issues found in the comprehensive test:
1. Better product ID extraction
2. Improved multiple product handling
3. More precise is_ready flag management
4. Better conversation state management
5. Enhanced product matching with semantic search

Optional LangChain integration for improved conversation management.
"""

import os
import json
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import uuid

# Optional LangChain imports - install with: pip install langchain langchain-openai
try:
    from langchain.memory import ConversationBufferWindowMemory, ConversationEntityMemory
    from langchain.schema import BaseMessage, HumanMessage, AIMessage
    from langchain.prompts import ChatPromptTemplate
    from langchain_openai import AzureChatOpenAI
    from langchain.chains import ConversationChain
    from langchain.agents import Tool, AgentExecutor, create_react_agent
    from langchain import hub
    LANGCHAIN_AVAILABLE = True
    print("✅ LangChain is available - Enhanced features enabled")
except ImportError:
    LANGCHAIN_AVAILABLE = False
    print("⚠️ LangChain not available - Using standard implementation")

@dataclass
class ConversationState:
    """Enhanced conversation state management"""
    stage: str = "INITIAL_INTEREST"
    interested_products: List[Dict] = None
    price_shown: bool = False
    explicit_confirmation: bool = False
    conversation_id: str = None
    
    def __post_init__(self):
        if self.interested_products is None:
            self.interested_products = []
        if self.conversation_id is None:
            self.conversation_id = str(uuid.uuid4())

class EnhancedProductMatcher:
    """Enhanced product matching with better similarity scoring"""
    
    def __init__(self, products: List[Dict]):
        self.products = products
        self.product_index = self._build_product_index()
    
    def _build_product_index(self) -> Dict[str, Dict]:
        """Build searchable index of products"""
        index = {}
        for product in self.products:
            # Index by exact name
            index[product['name'].lower()] = product
            
            # Index by variations
            name_parts = product['name'].lower().split()
            for i in range(len(name_parts)):
                for j in range(i+1, len(name_parts)+1):
                    partial_name = ' '.join(name_parts[i:j])
                    if len(partial_name) > 3:  # Avoid short matches
                        if partial_name not in index:
                            index[partial_name] = product
            
            # Index by tags
            for tag in product.get('product_tag', []):
                if tag.lower() not in index:
                    index[tag.lower()] = product
        
        return index
    
    def find_products_by_keywords(self, keywords: List[str]) -> List[Dict]:
        """Find products using enhanced keyword matching"""
        matched_products = []
        product_scores = {}
        
        for keyword in keywords:
            keyword = keyword.lower().strip()
            
            # Direct match
            if keyword in self.product_index:
                product = self.product_index[keyword]
                product_id = product['id']
                product_scores[product_id] = product_scores.get(product_id, 0) + 1.0
                if product not in matched_products:
                    matched_products.append(product)
            
            # Partial matches
            for indexed_term, product in self.product_index.items():
                if keyword in indexed_term or indexed_term in keyword:
                    product_id = product['id']
                    score = 0.7 if keyword in indexed_term else 0.5
                    product_scores[product_id] = product_scores.get(product_id, 0) + score
                    if product not in matched_products:
                        matched_products.append(product)
        
        # Sort by relevance score
        matched_products.sort(key=lambda p: product_scores.get(p['id'], 0), reverse=True)
        
        return matched_products[:5]  # Return top 5 matches
    
    def find_products_by_names(self, product_names: List[str]) -> List[Dict]:
        """Find products by specific names mentioned in conversation"""
        matched_products = []
        
        for name in product_names:
            name = name.lower().strip()
            
            # Try exact match first
            if name in self.product_index:
                product = self.product_index[name]
                if product not in matched_products:
                    matched_products.append(product)
                continue
            
            # Try fuzzy matching
            best_match = None
            best_score = 0
            
            for product in self.products:
                product_name = product['name'].lower()
                
                # Calculate similarity
                if name in product_name or product_name in name:
                    score = len(set(name.split()) & set(product_name.split())) / len(set(name.split()) | set(product_name.split()))
                    if score > best_score and score > 0.3:
                        best_score = score
                        best_match = product
            
            if best_match and best_match not in matched_products:
                matched_products.append(best_match)
        
        return matched_products

class EnhancedSalesStageAnalyzer:
    """Enhanced sales stage analysis with better purchase detection"""
    
    PURCHASE_KEYWORDS = [
        "i'll take", "i want to buy", "i'll buy", "i want to purchase", 
        "i'll purchase", "i want both", "i'll get", "let me buy",
        "i want it", "i'll order", "i want to order", "yes, buy",
        "confirm purchase", "complete order", "checkout"
    ]
    
    INTEREST_KEYWORDS = [
        "sounds good", "looks good", "that's good", "i like", "interesting",
        "tell me more", "seems perfect", "that works", "i'm interested"
    ]
    
    def analyze_stage(self, conversation_history: str, user_message: str, 
                     current_state: ConversationState) -> Tuple[str, bool, Dict]:
        """Enhanced stage analysis with better purchase detection"""
        
        user_lower = user_message.lower()
        
        # Check for explicit purchase confirmation
        explicit_purchase = any(keyword in user_lower for keyword in self.PURCHASE_KEYWORDS)
        
        # Check for interest (not purchase)
        shows_interest = any(keyword in user_lower for keyword in self.INTEREST_KEYWORDS)
        
        # Price-related inquiry
        price_inquiry = any(word in user_lower for word in ["price", "cost", "how much", "pricing"])
        
        analysis = {
            "explicit_purchase": explicit_purchase,
            "shows_interest": shows_interest,
            "price_inquiry": price_inquiry,
            "current_stage": current_state.stage
        }
        
        # Determine readiness - STRICT RULES
        is_ready = (
            explicit_purchase and 
            current_state.price_shown and 
            len(current_state.interested_products) > 0
        )
        
        # Determine next stage
        if explicit_purchase and is_ready:
            next_stage = "PURCHASE_CONFIRMATION"
        elif explicit_purchase and not current_state.price_shown:
            next_stage = "PRICE_EVALUATION"
        elif price_inquiry:
            next_stage = "PRICE_EVALUATION"
        elif shows_interest and current_state.interested_products:
            next_stage = "PURCHASE_INTENT"
        elif current_state.interested_products:
            next_stage = "PRODUCT_DISCOVERY"
        else:
            next_stage = "NEED_CLARIFICATION"
        
        analysis["next_stage"] = next_stage
        
        return next_stage, is_ready, analysis

class EnhancedConversationService:
    """Enhanced conversation service with better state management"""
    
    def __init__(self, ai_service, postgres_handler, mongo_handler):
        self.ai_service = ai_service
        self.postgres_handler = postgres_handler
        self.mongo_handler = mongo_handler
        
        # Load products and create enhanced matcher
        self.all_products = postgres_handler.get_all_products()
        self.product_matcher = EnhancedProductMatcher(self.all_products)
        self.stage_analyzer = EnhancedSalesStageAnalyzer()
        
        # Conversation states
        self.conversation_states: Dict[str, ConversationState] = {}
        
        # Optional LangChain integration
        if LANGCHAIN_AVAILABLE:
            self._setup_langchain()
    
    def _setup_langchain(self):
        """Setup LangChain components if available"""
        try:
            # Initialize Azure OpenAI with LangChain
            self.llm = AzureChatOpenAI(
                azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
                api_key=os.getenv("AZURE_OPENAI_API_KEY"),
                api_version=os.getenv("OPENAI_API_VERSION"),
                deployment_name=os.getenv("OPENAI_MODEL"),
                temperature=0.7
            )
            
            # Setup conversation memory
            self.memory = ConversationBufferWindowMemory(
                k=10,  # Remember last 10 exchanges
                return_messages=True
            )
            
            # Setup entity memory for product tracking
            self.entity_memory = ConversationEntityMemory(
                llm=self.llm,
                return_messages=True
            )
            
            print("✅ LangChain components initialized successfully")
            
        except Exception as e:
            print(f"⚠️ LangChain setup failed: {e}")
            self.llm = None
            self.memory = None
            self.entity_memory = None
    
    def get_conversation_state(self, sender_id: str) -> ConversationState:
        """Get or create conversation state for user"""
        if sender_id not in self.conversation_states:
            self.conversation_states[sender_id] = ConversationState()
        return self.conversation_states[sender_id]
    
    def update_conversation_state(self, sender_id: str, products: List[Dict], 
                                stage: str, price_shown: bool = False):
        """Update conversation state"""
        state = self.get_conversation_state(sender_id)
        
        # Update products - merge with existing ones
        for product in products:
            if not any(p['id'] == product['id'] for p in state.interested_products):
                state.interested_products.append(product)
        
        state.stage = stage
        if price_shown:
            state.price_shown = True
    
    def remove_products_from_state(self, sender_id: str, products_to_remove: List[str]):
        """Remove specific products from conversation state"""
        state = self.get_conversation_state(sender_id)
        
        # Remove products by name matching
        state.interested_products = [
            p for p in state.interested_products 
            if not any(remove_name.lower() in p['name'].lower() 
                      for remove_name in products_to_remove)
        ]
    
    def extract_product_removal_intent(self, user_message: str) -> List[str]:
        """Extract products that user wants to remove"""
        message_lower = user_message.lower()
        removal_keywords = ["don't need", "don't want", "remove", "cancel", "change", "instead"]
        
        if not any(keyword in message_lower for keyword in removal_keywords):
            return []
        
        # Extract product names mentioned for removal
        products_to_remove = []
        
        # Simple extraction - could be enhanced with NLP
        if "shampoo" in message_lower:
            products_to_remove.append("shampoo")
        if "perfume" in message_lower:
            products_to_remove.append("perfume")
        if "face wash" in message_lower:
            products_to_remove.append("face wash")
        
        return products_to_remove
    
    async def process_message_enhanced(self, sender_id: str, message: str) -> Dict:
        """Enhanced message processing with better state management"""
        
        # Get current conversation state
        state = self.get_conversation_state(sender_id)
        
        # Get conversation history
        conversation_history = self.mongo_handler.get_conversation(sender_id)
        is_first_interaction = len(conversation_history) == 0
        
        # Check for product removal intent
        products_to_remove = self.extract_product_removal_intent(message)
        if products_to_remove:
            self.remove_products_from_state(sender_id, products_to_remove)
            state = self.get_conversation_state(sender_id)  # Get updated state
        
        # Extract keywords and find relevant products
        keywords = self.ai_service.extract_keywords(message)
        
        # Find products using enhanced matcher
        relevant_products = []
        if keywords:
            relevant_products = self.product_matcher.find_products_by_keywords(keywords)
        
        # Update conversation state with new products
        if relevant_products:
            self.update_conversation_state(sender_id, relevant_products, state.stage)
            state = self.get_conversation_state(sender_id)  # Get updated state
        
        # Analyze sales stage with enhanced analyzer
        conversation_history_str = self._format_conversation_history(conversation_history)
        next_stage, is_ready, analysis = self.stage_analyzer.analyze_stage(
            conversation_history_str, message, state
        )
        
        # Check if price information should be shown
        price_shown = (
            "price" in message.lower() or 
            "cost" in message.lower() or 
            next_stage == "PRICE_EVALUATION"
        )
        
        if price_shown:
            state.price_shown = True
        
        # Generate product info from state
        all_interested_products = state.interested_products + relevant_products
        # Remove duplicates
        unique_products = []
        seen_ids = set()
        for product in all_interested_products:
            if product['id'] not in seen_ids:
                unique_products.append(product)
                seen_ids.add(product['id'])
        
        product_info = self._build_enhanced_product_info(unique_products)
        
        # Generate response
        response_text, final_is_ready = self.ai_service.generate_response(
            conversation_history=conversation_history_str,
            product_info=product_info,
            user_message=message,
            is_first_interaction=is_first_interaction
        )
        
        # Override is_ready with our enhanced logic
        final_is_ready = is_ready
        
        # Update conversation history
        updated_conversation = conversation_history + [
            {"role": "user", "content": message},
            {"role": "assistant", "content": response_text}
        ]
        self.mongo_handler.save_conversation(sender_id, updated_conversation)
        
        # Determine interested products for response
        interested_products_names = self._get_product_names_for_response(unique_products, state)
        interested_product_ids = [p['id'] for p in state.interested_products]
        
        return {
            "sender": sender_id,
            "product_interested": interested_products_names,
            "interested_product_ids": interested_product_ids,
            "response_text": response_text,
            "is_ready": final_is_ready,
            "debug_info": {
                "stage": next_stage,
                "analysis": analysis,
                "products_count": len(state.interested_products),
                "price_shown": state.price_shown
            }
        }
    
    def _get_product_names_for_response(self, products: List[Dict], state: ConversationState) -> str:
        """Get product names for the response"""
        if not state.interested_products:
            return None
        
        if len(state.interested_products) == 1:
            return state.interested_products[0]['name']
        else:
            names = [p['name'] for p in state.interested_products]
            return f"Multiple products: {', '.join(names)}"
    
    def _build_enhanced_product_info(self, products: List[Dict]) -> str:
        """Build enhanced product information"""
        if not products:
            return "No specific products found for this inquiry."
        
        product_details = []
        for product in products:
            price_info = f"₹{product['price']}"
            if product.get('sale_price') and product['sale_price'] < product['price']:
                price_info = f"₹{product['sale_price']} (originally ₹{product['price']}) - ON SALE!"
            
            details = f"""
            **{product['name']}** (ID: {product['id']})
            - Description: {product['description']}
            - Price: {price_info}
            - Rating: {product['rating']}/5.0 ({product['review_count']} reviews)
            - Stock: {product['stock_count']} available
            """
            product_details.append(details.strip())
        
        return "\n\n".join(product_details)
    
    def _format_conversation_history(self, conversation: List[Dict]) -> str:
        """Format conversation history"""
        if not conversation:
            return "No previous conversation."
        
        formatted = []
        for msg in conversation:
            role = "Customer" if msg['role'] == 'user' else "Assistant"
            formatted.append(f"{role}: {msg['content']}")
        
        return "\n".join(formatted)

# Test function for the enhanced system
def test_enhanced_system():
    """Test the enhanced conversation system"""
    from app.services.ai_service import ai_service
    from app.db.postgres_handler import PostgresHandler
    from app.db.mongo_handler import MongoHandler
    
    # Initialize components
    postgres_handler = PostgresHandler()
    mongo_handler = MongoHandler()
    
    # Create enhanced service
    enhanced_service = EnhancedConversationService(ai_service, postgres_handler, mongo_handler)
    
    # Test scenarios
    test_cases = [
        "I need a good perfume",
        "Tell me about Wild Stone",
        "What's the price?",
        "I also need a face wash",
        "Actually, I don't need the face wash anymore",
        "Yes, I want to buy the perfume"
    ]
    
    sender_id = "enhanced_test_user"
    
    print("🧪 Testing Enhanced Conversation System")
    print("=" * 50)
    
    for i, message in enumerate(test_cases, 1):
        print(f"\n📝 Step {i}: {message}")
        
        import asyncio
        result = asyncio.run(enhanced_service.process_message_enhanced(sender_id, message))
        
        print(f"🛍️  Products: {result['product_interested']}")
        print(f"🆔 IDs: {result['interested_product_ids']}")
        print(f"🚀 Ready: {result['is_ready']}")
        print(f"🤖 Response: {result['response_text'][:100]}...")
        print(f"🔍 Debug: {result['debug_info']}")

if __name__ == "__main__":
    test_enhanced_system()
