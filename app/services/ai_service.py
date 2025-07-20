from openai import AzureOpenAI
from app.core.config import settings
from typing import List, Tuple, Dict
import re
import os
import json

class AIService:
    def __init__(self):
        # Use both environment variable names for compatibility
        endpoint = settings.AZURE_OPENAI_ENDPOINT or os.getenv("ENDPOINT_URL")
        api_key = settings.AZURE_OPENAI_API_KEY
        deployment = settings.OPENAI_MODEL or os.getenv("DEPLOYMENT_NAME", "gpt-4.1-nano")
        
        # Initialize Azure OpenAI client with minimal configuration to avoid compatibility issues
        try:
            self.client = AzureOpenAI(
                azure_endpoint=endpoint,
                api_key=api_key,
                api_version="2024-02-15-preview"
            )
        except Exception as e:
            print(f"Warning: Azure OpenAI client failed to initialize: {e}")
            print("Falling back to mock responses for testing...")
            self.client = None
            
        self.deployment = deployment
        
        # Comprehensive business context based on your platform description
        self.business_context = """
        BUSINESS CONTEXT: We are a comprehensive personal care and beauty e-commerce platform, your ultimate destination for authentic, high-quality beauty and grooming products. Our curated marketplace brings together the finest selection from internationally renowned brands and cherished local manufacturers.

        MAIN PRODUCT CATEGORIES:
        - Premium Beauty Soaps & Body Care (moisturizing bars, antibacterial protection, luxury fragrances, French rose, almond oil, traditional ingredients like sandalwood and turmeric)
        - Professional Hair Care Solutions (anti-hair fall shampoos, silky smooth care formulations, anti-dandruff treatments, organic bio-certified options, strengthening formulas with vitamins)
        - Nourishing Hair Oils & Styling Products (pure coconut oils, lightweight almond formulas, ayurvedic amla preparations, herbal hibiscus treatments, traditional Bengali beauty secrets)
        - Captivating Fragrances & Perfumes (body sprays with pure perfume concentrates, chocolate-scented deodorants, premium woody perfumes, traditional Arabic attars with rose and oud)
        - Advanced Skincare Solutions (fairness creams with multivitamin complexes, gentle herbal face washes with neem and turmeric, specialized ayurvedic treatments)
        - Specialized Grooming Essentials (antibacterial protection, clinical-grade ingredients, natural extracts, traditional wisdom)

        FEATURED BRANDS:
        - International: Lux, Dove, Pantene, Head & Shoulders, Sunsilk, Herbal Essences, Garnier, AXE, Fogg, Wild Stone, Himalaya
        - Local Bangladesh: Keya Seth, Tibbet (representing regional wisdom and traditional formulations)

        TARGET CUSTOMERS: Beauty enthusiasts, grooming-conscious individuals, traditional beauty lovers, professional users, families seeking authentic products

        PRODUCT FOCUS KEYWORDS: beauty, skincare, hair care, fragrance, soap, shampoo, oil, perfume, grooming, traditional, herbal, natural, premium, luxury, authentic, moisturizing, anti-aging, protection, nourishment

        VALUE PROPOSITION: Perfect balance of effectiveness, quality, and value combining international innovation with traditional regional wisdom in beauty care.

        INSTRUCTION: From customer messages, extract ONLY keywords that relate to personal care, beauty, grooming, and our product categories. Focus on purchase intent, product features, quality indicators, and specific beauty needs.
        """

    async def extract_keywords_with_llm(self, user_message: str) -> List[str]:
        """
        Extract relevant keywords from user message using LLM with business context.
        
        Args:
            user_message: The user's input message
            
        Returns:
            List of extracted keywords
        """
        # If Azure OpenAI client is not available, use mock response for testing
        if not self.client:
            print("Using mock keyword extraction for testing...")
            # Mock response based on the test message
            if "scent" in user_message.lower() or "perfume" in user_message.lower() or "fragrance" in user_message.lower():
                return ["scent", "perfume", "fragrance", "hair", "oil"]
            else:
                return ["beauty", "skin", "care"]
        messages = [
            {
                "role": "system",
                "content": """You are an expert keyword extraction specialist for a personal care and beauty e-commerce platform.
                Your job is to identify ONLY the keywords from customer messages that indicate interest in beauty, skincare, hair care, fragrances, or grooming products.
                
                Extract 3-8 most relevant keywords that indicate:
                - Product categories (soap, shampoo, perfume, face wash, hair oil, etc.)
                - Product features (moisturizing, anti-dandruff, long-lasting, herbal, organic, etc.)
                - Beauty concerns (hair fall, acne, dry skin, dandruff, etc.)
                - Purchase intent (buy, need, looking for, want, recommend, etc.)
                - Quality/price indicators (premium, luxury, affordable, quality, etc.)
                - Brand preferences (natural, herbal, traditional, international, etc.)
                
                Return ONLY the keywords as a comma-separated list, no explanations."""
            },
            {
                "role": "user",
                "content": f"""
                {self.business_context}
                
                CUSTOMER MESSAGE: "{user_message}"
                
                Extract the most relevant beauty and personal care keywords from this message.
                Maximum 8 keywords, comma-separated.
                """
            }
        ]
        
        try:
            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=messages,
                max_tokens=100,
                temperature=0.1,  # Low temperature for consistent extraction
            )
            
            keywords_text = response.choices[0].message.content.strip()
            keywords = [kw.strip().lower() for kw in keywords_text.split(',') if kw.strip()]
            
            # Clean and filter keywords
            filtered_keywords = []
            for keyword in keywords:
                # Remove punctuation and extra spaces
                clean_keyword = re.sub(r'[^\w\s-]', '', keyword).strip()
                if len(clean_keyword) > 2:  # Only keep meaningful keywords
                    filtered_keywords.append(clean_keyword)
            
            return filtered_keywords[:8]  # Maximum 8 keywords
            
        except Exception as e:
            print(f"Error extracting keywords with LLM: {e}")
            return self._fallback_keyword_extraction(user_text)

    def find_matching_products_with_llm(self, keywords: List[str], all_products: List[Dict]) -> List[Tuple[Dict, float]]:
        """
        Use LLM to find product matches by comparing keywords with product tags
        This approach scales to millions of products
        """
        if not keywords or not all_products:
            return []
        
        # Prepare product data for LLM analysis
        product_data_for_llm = []
        for product in all_products:
            if not product.get('is_active', True):
                continue
                
            product_tags = product.get('product_tag', [])
            if product_tags:
                product_info = {
                    "id": product['id'],
                    "name": product['name'],
                    "tags": product_tags,
                    "rating": product.get('rating', 0),
                    "price": product.get('price', 0)
                }
                product_data_for_llm.append(product_info)
        
        if not product_data_for_llm:
            return []
        
        # Split into batches for large product catalogs
        batch_size = 50  # Process 50 products at a time to avoid token limits
        all_matches = []
        
        for i in range(0, len(product_data_for_llm), batch_size):
            batch = product_data_for_llm[i:i + batch_size]
            batch_matches = self._process_product_batch_with_llm(keywords, batch, all_products)
            all_matches.extend(batch_matches)
        
        # Sort by similarity score and return top matches
        all_matches.sort(key=lambda x: x[1], reverse=True)
        return all_matches[:5]  # Return top 5 matches

    def _process_product_batch_with_llm(self, keywords: List[str], product_batch: List[Dict], all_products: List[Dict]) -> List[Tuple[Dict, float]]:
        """Process a batch of products with LLM for similarity matching"""
        
        # Create structured product list for LLM
        products_text = ""
        for i, product in enumerate(product_batch, 1):
            tags_str = ", ".join(product['tags'])
            products_text += f"{i}. ID: {product['id']} | Name: {product['name']} | Tags: [{tags_str}]\n"
        
        messages = [
            {
                "role": "system",
                "content": """You are an expert product matching specialist for a beauty and personal care e-commerce platform. 
                Analyze customer keywords against product tags to find the most relevant beauty products.
                
                Score each product based on how well the customer keywords match the product tags:
                - 95-100: Perfect match (multiple exact keyword-tag matches + high relevance)
                - 85-94: Excellent match (several exact matches + semantic similarity like "scent"="perfume")
                - 75-84: Good match (related concepts in same category like "moisturizing"="nourishing")
                - 65-74: Fair match (loosely related, same general category)
                - Below 65: Poor match (unrelated to customer needs)
                
                Consider semantic similarity in beauty context:
                - "scent", "fragrance", "perfume", "cologne" are all related
                - "moisturizing", "nourishing", "hydrating" are similar
                - "hair fall", "hair loss", "breakage" are related
                - "acne", "pimples", "blemishes" are similar
                - "fairness", "brightening", "whitening" are related
                
                Return ONLY a JSON list with product IDs and scores for products scoring 65+.
                Format: [{"id": "product_id", "score": 85}, ...]"""
            },
            {
                "role": "user",
                "content": f"""
                CUSTOMER KEYWORDS: {', '.join(keywords)}
                
                BEAUTY PRODUCTS TO ANALYZE:
                {products_text}
                
                Analyze each product and return JSON with product IDs and similarity scores (65-100).
                Focus on beauty and personal care relevance to customer needs.
                """
            }
        ]
        
        try:
            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=messages,
                max_tokens=300,
                temperature=0.1,
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # Parse JSON response
            matches_data = json.loads(response_text)
            
            # Convert to required format
            matches = []
            product_lookup = {p['id']: p for p in all_products}
            
            for match in matches_data:
                product_id = match.get('id')
                score = float(match.get('score', 0))
                
                if product_id in product_lookup and score >= 65:
                    product = product_lookup[product_id]
                    matches.append((product, score))
            
            return matches
            
        except (json.JSONDecodeError, KeyError, Exception) as e:
            print(f"Error processing product batch with LLM: {e}")
            # Fallback to simple keyword matching for this batch
            return self._fallback_product_matching(keywords, product_batch, all_products)

    def _fallback_product_matching(self, keywords: List[str], product_batch: List[Dict], all_products: List[Dict]) -> List[Tuple[Dict, float]]:
        """Fallback method using simple similarity calculation"""
        matches = []
        product_lookup = {p['id']: p for p in all_products}
        
        for product_info in product_batch:
            product_id = product_info['id']
            if product_id not in product_lookup:
                continue
                
            product = product_lookup[product_id]
            product_tags = product.get('product_tag', [])
            
            # Simple keyword-tag matching
            score = self.calculate_similarity_score(keywords, product_tags) * 100
            
            if score >= 65:
                matches.append((product, score))
        
        return matches

    def _fallback_keyword_extraction(self, text: str) -> List[str]:
        """Fallback method using simple pattern matching for beauty terms"""
        # Extract meaningful words (3+ characters)
        words = re.findall(r'\b\w{3,}\b', text.lower())
        
        # Filter beauty and personal care related terms
        beauty_terms = []
        beauty_keywords = [
            'soap', 'shampoo', 'oil', 'perfume', 'cologne', 'fragrance', 'scent',
            'moisturizing', 'dry', 'oily', 'sensitive', 'acne', 'dandruff',
            'hair', 'skin', 'face', 'body', 'beauty', 'care', 'wash',
            'premium', 'luxury', 'natural', 'herbal', 'organic',
            'buy', 'need', 'want', 'looking', 'recommend'
        ]
        
        for word in words:
            if any(term in word for term in beauty_keywords):
                beauty_terms.append(word)
        
        return beauty_terms[:5] if beauty_terms else words[:5]

    def get_keywords(self, text: str, product_context: str) -> List[str]:
        """Extract relevant keywords from user message based on product context - LEGACY METHOD"""
        # This method is kept for backward compatibility
        # New implementation uses extract_keywords_with_llm
        return self.extract_keywords_with_llm(text)

    def calculate_similarity_score(self, keywords: List[str], product_tags: List[str]) -> float:
        """Calculate similarity score between keywords and product tags"""
        if not keywords or not product_tags:
            return 0.0
        
        # Convert to lowercase for comparison
        keywords_lower = [k.lower() for k in keywords]
        tags_lower = [t.lower() for t in product_tags]
        
        # Calculate exact matches
        exact_matches = len(set(keywords_lower) & set(tags_lower))
        
        # Calculate partial matches (keywords contained in tags or vice versa)
        partial_matches = 0
        for keyword in keywords_lower:
            for tag in tags_lower:
                if keyword in tag or tag in keyword:
                    partial_matches += 0.5
                    break
        
        total_score = exact_matches + partial_matches
        max_possible = max(len(keywords_lower), len(tags_lower))
        
        return min(total_score / max_possible, 1.0) if max_possible > 0 else 0.0

    def check_readiness_to_buy(self, conversation_history: str, user_message: str) -> bool:
        """Check if user is ready to make a purchase"""
        messages = [
            {
                "role": "system",
                "content": """You are an expert at determining customer purchase intent. 
                Analyze the conversation to determine if the customer is ready to buy.
                Look for signals like: asking about purchase process, expressing definite interest, 
                asking about payment/delivery, saying they want to buy, etc."""
            },
            {
                "role": "user",
                "content": f"""
                Conversation History: {conversation_history}
                Latest Message: {user_message}
                
                Is the customer ready to proceed with a purchase? 
                Respond with only 'true' or 'false'.
                """
            }
        ]
        
        try:
            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=messages,
                max_tokens=10,
                temperature=0.1,
            )
            result = response.choices[0].message.content.strip().lower()
            return result == 'true'
        except Exception as e:
            print(f"Error checking readiness: {e}")
            return False

    def generate_response(self, conversation_history: str, product_info: str, user_message: str, is_first_interaction: bool = False) -> Tuple[str, bool]:
        """Generate contextual response based on conversation stage and user interest"""
        
        # Check if user is ready to buy
        is_ready = self.check_readiness_to_buy(conversation_history, user_message)
        
        if is_ready:
            messages = [
                {
                    "role": "system",
                    "content": "The customer is ready to buy. Generate a helpful response to assist with their purchase."
                },
                {
                    "role": "user", 
                    "content": f"User message: {user_message}\nAvailable products: {product_info}\nHelp them proceed with their purchase."
                }
            ]
        elif is_first_interaction:
            messages = [
                {
                    "role": "system",
                    "content": """You are a warm, friendly sales assistant for a premium product store. 
                    This is your first interaction with this customer. Be welcoming and engaging.
                    Your goal is to understand their needs and guide them to the right products."""
                },
                {
                    "role": "user",
                    "content": f"""
                    Customer's first message: {user_message}
                    Available products: {product_info}
                    
                    Provide a warm welcome and try to understand what they're looking for.
                    Be conversational and helpful, not pushy.
                    """
                }
            ]
        else:
            messages = [
                {
                    "role": "system", 
                    "content": """You are a friendly and persuasive sales assistant. Your goals:
                    1. Be warm and personable
                    2. Understand customer needs
                    3. Present relevant products compellingly  
                    4. Handle objections gracefully
                    5. Guide toward purchase when appropriate
                    6. If they seem uninterested, suggest similar products
                    7. Stay professional and helpful always"""
                },
                {
                    "role": "user",
                    "content": f"""
                    Conversation so far: {conversation_history}
                    Latest message: {user_message}
                    Relevant products: {product_info}
                    
                    Generate an appropriate response. Be persuasive but not pushy.
                    If they're uninterested, try suggesting alternatives or ask what they're looking for.
                    """
                }
            ]
        
        try:
            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=messages,
                max_tokens=200,
                temperature=0.7,
            )
            
            response_text = response.choices[0].message.content.strip()
            return response_text, is_ready
            
        except Exception as e:
            print(f"Error generating response: {e}")
            fallback_response = "I'd be happy to help you find what you're looking for. Could you tell me more about what interests you?"
            return fallback_response, False

ai_service = AIService()
