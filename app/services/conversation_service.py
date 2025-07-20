
from app.db.mongo_handler import mongo_handler
from app.db.postgres_handler import postgres_handler
from app.services.ai_service import ai_service
from app.models.schemas import Message
from typing import List, Dict

class ConversationService:
    def process_message(self, message: Message):
        # 1. Get conversation history (limit to last 10 conversations)
        conversation_data = mongo_handler.get_conversation(message.sender)
        full_conversation = conversation_data['conversation'] if conversation_data else []
        
        # Keep only last 10 exchanges (20 messages: 10 user + 10 assistant)
        conversation_history = full_conversation[-20:] if len(full_conversation) > 20 else full_conversation
        
        # Check if this is first interaction
        is_first_interaction = len(full_conversation) == 0

        # 2. Get product context for keyword extraction
        all_products = postgres_handler.get_all_products()
        product_context = self._build_product_context(all_products)

        # 3. Extract keywords from user message
        keywords = ai_service.get_keywords(message.text, product_context)

        # 4. Find relevant products based on similarity scoring
        relevant_products = self._find_relevant_products(keywords, all_products)
        
        # 5. Build product information for AI
        product_info = self._build_product_info(relevant_products)

        # 6. Generate response
        conversation_history_str = self._format_conversation_history(conversation_history)
        response_text, is_ready = ai_service.generate_response(
            conversation_history=conversation_history_str,
            product_info=product_info,
            user_message=message.text,
            is_first_interaction=is_first_interaction
        )

        # 7. Save updated conversation
        updated_conversation = full_conversation + [
            {"role": "user", "content": message.text},
            {"role": "assistant", "content": response_text}
        ]
        mongo_handler.save_conversation(message.sender, updated_conversation)

        # 8. Determine most interested product
        product_interested = self._determine_interested_product(relevant_products, keywords)

        return {
            "sender": message.sender,
            "product_interested": product_interested,
            "response_text": response_text,
            "isReady": is_ready,
        }

    def _build_product_context(self, products: List[Dict]) -> str:
        """Build general product context for keyword extraction"""
        context_parts = []
        for product in products:
            tags = product.get('product_tag', product.get('tags', []))
            context_parts.append(f"- {product['name']}: {', '.join(tags)}")
        return "\n".join(context_parts)

    def _find_relevant_products(self, keywords: List[str], all_products: List[Dict]) -> List[Dict]:
        """Find products with similarity score >= 70%"""
        relevant_products = []
        
        for product in all_products:
            product_tags = product.get('product_tag', product.get('tags', []))
            similarity_score = ai_service.calculate_similarity_score(keywords, product_tags)
            
            if similarity_score >= 0.7:  # 70% threshold
                product['similarity_score'] = similarity_score
                relevant_products.append(product)
        
        # Sort by similarity score (highest first)
        relevant_products.sort(key=lambda x: x.get('similarity_score', 0), reverse=True)
        
        # Return top 3 most relevant products
        return relevant_products[:3]

    def _build_product_info(self, products: List[Dict]) -> str:
        """Build detailed product information for AI response generation"""
        if not products:
            return "We have a variety of quality products available. Let me know what you're interested in and I'll help you find the perfect match!"
        
        product_details = []
        for product in products:
            price_info = f"₹{product['price']}"
            if product.get('sale_price'):
                price_info = f"₹{product['sale_price']} (was ₹{product['price']})"
            
            details = f"""
            - **{product['name']}**: {product['description']}
              Price: {price_info}
              Rating: {product['rating']}/5 ({product['review_count']} reviews)
              Stock: {product['stock_count']} available
            """
            product_details.append(details.strip())
        
        return "\n\n".join(product_details)

    def _format_conversation_history(self, conversation: List[Dict]) -> str:
        """Format conversation history for AI context"""
        if not conversation:
            return "No previous conversation."
        
        formatted = []
        for msg in conversation:
            role = "Customer" if msg['role'] == 'user' else "Assistant"
            formatted.append(f"{role}: {msg['content']}")
        
        return "\n".join(formatted)

    def _determine_interested_product(self, relevant_products: List[Dict], keywords: List[str]) -> str:
        """Determine which product the customer is most interested in"""
        if not relevant_products:
            return None
        
        # Return the highest scored product
        top_product = relevant_products[0]
        return top_product['name']

conversation_service = ConversationService()
