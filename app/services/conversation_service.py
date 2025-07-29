
from app.db.mongo_handler import mongo_handler
from app.db.postgres_handler import postgres_handler
from app.services.ai_service import ai_service
from app.models.schemas import Message
from typing import List, Dict
import logging

class ConversationService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # Add conversation state tracking for multiple products
        self.conversation_states = {}  # sender_id -> {"products": [product_objects], "stage": "stage_name"}
    
    async def process_message(self, message: Message):
        # 1. Get conversation history (limit to last 10 conversations)
        conversation_data = mongo_handler.get_conversation(message.sender)
        full_conversation = conversation_data['conversation'] if conversation_data else []
        
        # Keep only last 10 exchanges (20 messages: 10 user + 10 assistant)
        conversation_history = full_conversation[-20:] if len(full_conversation) > 20 else full_conversation
        
        # Check if this is first interaction
        is_first_interaction = len(full_conversation) == 0

        # 1.5. NEW: Check for product removal intent and handle it
        removal_keywords = self._detect_product_removal_intent(message.text)
        if removal_keywords:
            self._remove_products_from_state(message.sender, removal_keywords)

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
        
        # 5.5. NEW: Update conversation state with newly found products
        if relevant_products:
            self._update_conversation_state(message.sender, relevant_products, sales_analysis.get('current_stage'))
        
        # 6. NEW: Apply price range filtering if customer mentioned budget constraints
        price_range = sales_analysis.get('price_range_mentioned')
        if price_range and relevant_products:
            self.logger.info(f"Filtering products by price range: {price_range}")
            relevant_products = ai_service.filter_products_by_price_range(relevant_products, price_range)
            self.logger.info(f"After price filtering: {len(relevant_products)} products remain")
        
        # 6.5. NEW: Get all products from conversation state for comprehensive tracking
        conversation_state = self._get_conversation_state(message.sender)
        all_interested_products = conversation_state['products']
        
        # Combine current relevant products with stored state products (remove duplicates)
        combined_products = list(all_interested_products)  # Start with state products
        for product in relevant_products:
            if not any(p['id'] == product['id'] for p in combined_products):
                combined_products.append(product)
        
        # 7. Build product information for AI using all tracked products
        product_info = self._build_product_info(combined_products)

        # 8. Generate response using enhanced sales funnel
        response_text, is_ready = ai_service.generate_response(
            conversation_history=conversation_history_str,
            product_info=product_info,
            user_message=message.text,
            is_first_interaction=is_first_interaction
        )

        # 9. Save updated conversation
        updated_conversation = full_conversation + [
            {"role": "user", "content": message.text},
            {"role": "assistant", "content": response_text}
        ]
        mongo_handler.save_conversation(message.sender, updated_conversation)

        # 10. NEW: Determine most interested product(s) using conversation state
        product_interested = self._determine_interested_product_with_state(message.sender, sales_analysis, is_ready)
        
        # 11. NEW: Extract product IDs from conversation state for better tracking
        interested_product_ids = self._extract_product_ids_from_state(message.sender)

        return {
            "sender": message.sender,
            "product_interested": product_interested,  # Product names for display
            "interested_product_ids": interested_product_ids,  # Product IDs for Routing Agent
            "response_text": response_text,
            "is_ready": is_ready,
        }

    def _build_product_context(self, products: List[Dict]) -> str:
        """Build general product context for keyword extraction - LEGACY METHOD"""
        # This method is kept for backward compatibility
        # New implementation uses LLM-based business context in ai_service
        context_parts = []
        for product in products:
            tags = product.get('product_tag', product.get('tags', []))
            context_parts.append(f"- {product['name']}: {', '.join(tags)}")
        return "\n".join(context_parts)

    def _find_relevant_products(self, keywords: List[str], all_products: List[Dict]) -> List[Dict]:
        """Find products with similarity score >= 70% - LEGACY METHOD"""
        # This method is kept for backward compatibility
        # New implementation uses ai_service.find_matching_products_with_llm
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
            return """We have a comprehensive collection of premium beauty and personal care products including:
            
            - Premium Beauty Soaps & Body Care (moisturizing bars, luxury fragrances, traditional ingredients)
            - Professional Hair Care Solutions (anti-hair fall shampoos, organic treatments, strengthening formulas)
            - Nourishing Hair Oils & Styling Products (coconut oils, ayurvedic amla preparations, herbal treatments)
            - Captivating Fragrances & Perfumes (body sprays, premium woody perfumes, traditional attars)
            - Advanced Skincare Solutions (fairness creams, gentle herbal face washes, ayurvedic treatments)
            - Specialized Grooming Essentials (antibacterial protection, natural extracts)
            
            Featured brands include Lux, Dove, Pantene, Head & Shoulders, Garnier, AXE, Fogg, Wild Stone, and local favorites like Keya Seth and Tibbet.
            
            What specific beauty or personal care needs can I help you with today?"""
        
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

    def _build_product_info(self, products: List[Dict]) -> str:
        """Build comprehensive product information including prices for AI context"""
        if not products:
            return """No specific products found for this inquiry. Our beauty and personal care catalog includes:
            
            Popular Categories:
            - Premium perfumes and fragrances 
            - Skincare and beauty soaps
            - Hair care products (shampoos, oils)
            - Personal care items (deodorants, body sprays)
            
            What specific beauty or personal care needs can I help you with today?"""
        
        product_details = []
        for product in products:
            # Price information with sale prices
            price_info = f"₹{product['price']}"
            if product.get('sale_price') and product['sale_price'] < product['price']:
                price_info = f"₹{product['sale_price']} (originally ₹{product['price']}) - ON SALE!"
            
            # Stock availability
            stock_status = "In stock" if product['stock_count'] > 0 else "Limited stock"
            if product['stock_count'] > 50:
                stock_status = "Well stocked"
            elif product['stock_count'] <= 10:
                stock_status = "Only few left!"
            
            # Product tags for better matching
            tags = product.get('product_tag', [])
            tags_info = f"Tags: {', '.join(tags[:8])}" if tags else ""  # Show first 8 tags
            
            details = f"""
            **{product['name']}** (ID: {product['id']})
            - Description: {product['description']}
            - Price: {price_info}
            - Rating: {product['rating']}/5.0 ({product['review_count']} customer reviews)
            - Availability: {stock_status} ({product['stock_count']} units)
            - {tags_info}
            """
            product_details.append(details.strip())
        
        return "\n\n".join(product_details)

    def _get_conversation_state(self, sender_id: str) -> Dict:
        """Get conversation state for a user"""
        if sender_id not in self.conversation_states:
            self.conversation_states[sender_id] = {"products": [], "stage": "INITIAL_INTEREST"}
        return self.conversation_states[sender_id]
    
    def _update_conversation_state(self, sender_id: str, new_products: List[Dict], stage: str = None):
        """Update conversation state with new products"""
        state = self._get_conversation_state(sender_id)
        
        # Add new products, avoiding duplicates
        for product in new_products:
            if not any(p['id'] == product['id'] for p in state['products']):
                state['products'].append(product)
        
        if stage:
            state['stage'] = stage
        
        self.logger.info(f"Updated conversation state for {sender_id}: {len(state['products'])} products, stage: {state.get('stage')}")
    
    def _remove_products_from_state(self, sender_id: str, products_to_remove: List[str]):
        """Remove products from conversation state based on keywords"""
        state = self._get_conversation_state(sender_id)
        
        original_count = len(state['products'])
        
        # Remove products that match removal keywords
        state['products'] = [
            p for p in state['products']
            if not any(remove_keyword.lower() in p['name'].lower() 
                      for remove_keyword in products_to_remove)
        ]
        
        removed_count = original_count - len(state['products'])
        if removed_count > 0:
            self.logger.info(f"Removed {removed_count} products from state for {sender_id}")
    
    def _detect_product_removal_intent(self, message: str) -> List[str]:
        """Detect if user wants to remove certain products"""
        message_lower = message.lower()
        removal_phrases = ["don't need", "don't want", "remove", "cancel", "not interested in", "skip"]
        
        if not any(phrase in message_lower for phrase in removal_phrases):
            return []
        
        # Extract product types/names that user wants to remove
        removal_keywords = []
        
        # Common product categories
        product_categories = ["shampoo", "perfume", "face wash", "soap", "oil", "cream", "deodorant"]
        
        for category in product_categories:
            if category in message_lower and any(phrase in message_lower for phrase in removal_phrases):
                removal_keywords.append(category)
        
        return removal_keywords

    def _format_conversation_history(self, conversation: List[Dict]) -> str:
        """Format conversation history for AI context"""
        if not conversation:
            return "No previous conversation."
        
        formatted = []
        for msg in conversation:
            role = "Customer" if msg['role'] == 'user' else "Assistant"
            formatted.append(f"{role}: {msg['content']}")
        
        return "\n".join(formatted)

    def _determine_interested_product_enhanced(self, relevant_products: List[Dict], keywords: List[str], sales_analysis: Dict, is_ready: bool = False) -> str:
        """Enhanced method to determine product interest using sales analysis"""
        
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
                    if analysis_product.lower() in product['name'].lower():
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
        
        # PRIORITY 4: Fallback to original logic based on relevant products
        if not relevant_products:
            return None
            
        return self._determine_interested_product(relevant_products, keywords)

    def _extract_product_ids(self, relevant_products: List[Dict], sales_analysis: Dict, product_interested: str) -> List[str]:
        """Extract product IDs for the products customer is interested in"""
        if not product_interested:
            return []
        
        interested_product_ids = []
        
        # Get products from sales analysis first
        interested_products_from_analysis = sales_analysis.get('interested_products', [])
        
        # If we have specific product names from analysis or product_interested
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
        
        # Find matching product IDs from relevant_products
        for product_name in product_names_to_find:
            for product in relevant_products:
                if (product_name.lower() in product['name'].lower() or 
                    product['name'].lower() in product_name.lower()):
                    if product.get('id') and product['id'] not in interested_product_ids:
                        interested_product_ids.append(product['id'])
                    break
        
        return interested_product_ids

    def _determine_interested_product_with_state(self, sender_id: str, sales_analysis: Dict, is_ready: bool = False) -> str:
        """Determine interested products using conversation state"""
        state = self._get_conversation_state(sender_id)
        
        # PRIORITY 1: If ready to buy, show products from state
        if is_ready and state['products']:
            if len(state['products']) == 1:
                return state['products'][0]['name']
            else:
                names = [p['name'] for p in state['products']]
                return f"Multiple products: {', '.join(names)}"
        
        # PRIORITY 2: Get products from sales analysis
        interested_products_from_analysis = sales_analysis.get('interested_products', [])
        
        # PRIORITY 3: If we have products in state, return them
        if state['products']:
            if len(state['products']) == 1:
                return state['products'][0]['name']
            else:
                names = [p['name'] for p in state['products']]
                return f"Multiple products: {', '.join(names)}"
        
        # PRIORITY 4: Fallback to analysis products
        if interested_products_from_analysis:
            if len(interested_products_from_analysis) == 1:
                return interested_products_from_analysis[0]
            else:
                return f"Multiple products: {', '.join(interested_products_from_analysis)}"
        
        return None
    
    def _extract_product_ids_from_state(self, sender_id: str) -> List[str]:
        """Extract product IDs from conversation state"""
        state = self._get_conversation_state(sender_id)
        return [product['id'] for product in state['products']]

    def _determine_interested_product(self, relevant_products: List[Dict], keywords: List[str]) -> str:
        """Enhanced method to determine which product(s) the customer is most interested in"""
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
            return f"{', '.join(product_names)}"
        else:
            # Single product case
            return relevant_products[0]['name']

conversation_service = ConversationService()
