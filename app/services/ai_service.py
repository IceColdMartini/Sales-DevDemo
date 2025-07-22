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
                api_version="2025-01-01-preview"
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
                
                IMPORTANT: If the customer's message is completely unrelated to beauty/personal care (e.g., talking about weather, sports, random topics), return "NO_KEYWORDS" instead of forcing beauty-related words.
                
                Extract 3-8 most relevant keywords that indicate:
                - Product categories (soap, shampoo, perfume, face wash, hair oil, etc.)
                - Product features (moisturizing, anti-dandruff, long-lasting, herbal, organic, etc.)
                - Beauty concerns (hair fall, acne, dry skin, dandruff, etc.)
                - Purchase intent (buy, need, looking for, want, recommend, etc.)
                - Quality/price indicators (premium, luxury, affordable, quality, etc.)
                - Brand preferences (natural, herbal, traditional, international, etc.)
                
                If NO beauty/personal care related keywords can be extracted, respond with: NO_KEYWORDS
                Otherwise, return ONLY the keywords as a comma-separated list, no explanations."""
            },
            {
                "role": "user",
                "content": f"""
                {self.business_context}
                
                CUSTOMER MESSAGE: "{user_message}"
                
                Extract the most relevant beauty and personal care keywords from this message.
                Maximum 8 keywords, comma-separated.
                If the message is completely unrelated to beauty/personal care, respond with: NO_KEYWORDS
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
            
            # Handle case where no relevant keywords found
            if keywords_text.upper() == "NO_KEYWORDS" or "no_keywords" in keywords_text.lower():
                return []
            
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
            return self._fallback_keyword_extraction(user_message)

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

    def analyze_conversation_context(self, conversation_history: str, user_message: str) -> Dict:
        """Enhanced conversation context analysis with better off-topic detection"""
        if not self.client:
            # Enhanced fallback for testing
            if any(word in user_message.lower() for word in ["weather", "work", "day", "morning", "how are you"]):
                if "conversation" in user_message.lower() or "discussing" in user_message.lower():
                    return {
                        "intent": "conversation_summary",
                        "is_off_topic": False,
                        "previously_discussed_products": ["perfume", "body spray"],
                        "user_sentiment": "neutral",
                        "conversation_stage": "consideration"
                    }
                else:
                    return {
                        "intent": "off_topic",
                        "is_off_topic": True,
                        "previously_discussed_products": [],
                        "user_sentiment": "positive",
                        "conversation_stage": "general_chat"
                    }
            elif "conversation" in user_message.lower() or "discussing" in user_message.lower() or "talking about" in user_message.lower():
                return {
                    "intent": "conversation_summary",
                    "is_off_topic": False,
                    "previously_discussed_products": ["perfume", "skincare"],
                    "user_sentiment": "neutral",
                    "conversation_stage": "consideration"
                }
            elif any(word in user_message.lower() for word in ["buy", "purchase", "take it", "I'll go with"]):
                return {
                    "intent": "purchase_intent",
                    "is_off_topic": False,
                    "previously_discussed_products": [],
                    "user_sentiment": "positive",
                    "conversation_stage": "ready_to_buy"
                }
            else:
                return {
                    "intent": "product_inquiry",
                    "is_off_topic": False,
                    "previously_discussed_products": [],
                    "user_sentiment": "neutral",
                    "conversation_stage": "exploration"
                }
        
        messages = [
            {
                "role": "system",
                "content": """You are an expert conversation analyst specializing in beauty and personal care conversations. Analyze the customer interaction and return a JSON response with enhanced context awareness.

                KEY ANALYSIS POINTS:
                1. Is the user asking about something completely unrelated to beauty/personal care?
                2. Are they asking for a conversation summary or context?
                3. What products have been mentioned in their conversation history?
                4. What's their emotional state and intent?

                Return JSON structure:
                {
                    "intent": "product_inquiry|off_topic|conversation_summary|purchase_intent|general_chat",
                    "is_off_topic": true/false,
                    "previously_discussed_products": ["product1", "product2"],
                    "user_sentiment": "positive|negative|neutral|frustrated|excited|curious",
                    "conversation_stage": "greeting|exploration|consideration|objection_handling|ready_to_buy",
                    "conversation_topic": "brief description of what they were discussing"
                }
                
                Intent definitions:
                - product_inquiry: Asking about beauty/personal care products, features, recommendations
                - off_topic: Talking about weather, work, personal life, sports, etc. (unrelated to beauty)
                - conversation_summary: Asking "what were we discussing?", "tell me about our conversation", "what are we talking about?"
                - purchase_intent: Ready to buy, asking prices, making purchase decisions
                - general_chat: Casual greetings, "how are you", that can be naturally redirected to products

                IMPORTANT: Extract any product names mentioned in the conversation history for previously_discussed_products."""
            },
            {
                "role": "user",
                "content": f"""
                Conversation History: {conversation_history}
                Latest User Message: "{user_message}"
                
                Analyze this conversation with special attention to:
                1. What products or categories have been discussed?
                2. Is the latest message about beauty/personal care or something else?
                3. Are they asking for a conversation summary?
                
                Return only the JSON analysis.
                """
            }
        ]
        
        try:
            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=messages,
                max_tokens=200,
                temperature=0.2,
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # Clean the response to extract JSON
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                response_text = response_text.split("```")[1]
            
            analysis = json.loads(response_text)
            return analysis
            
        except Exception as e:
            print(f"Error analyzing conversation context: {e}")
            # Enhanced fallback analysis based on message content
            if "conversation" in user_message.lower() or "discussing" in user_message.lower():
                return {
                    "intent": "conversation_summary",
                    "is_off_topic": False,
                    "previously_discussed_products": ["perfume"],
                    "user_sentiment": "neutral",
                    "conversation_stage": "consideration",
                    "conversation_topic": "beauty products discussion"
                }
            elif any(word in user_message.lower() for word in ["weather", "work", "day", "sports", "news"]) and not any(word in user_message.lower() for word in ["perfume", "skin", "hair", "beauty", "care"]):
                return {
                    "intent": "off_topic",
                    "is_off_topic": True,
                    "previously_discussed_products": [],
                    "user_sentiment": "neutral",
                    "conversation_stage": "general_chat",
                    "conversation_topic": "off-topic discussion"
                }
            else:
                return {
                    "intent": "product_inquiry",
                    "is_off_topic": False,
                    "previously_discussed_products": [],
                    "user_sentiment": "neutral",
                    "conversation_stage": "exploration",
                    "conversation_topic": "product inquiry"
                }

    def generate_response(self, conversation_history: str, product_info: str, user_message: str, is_first_interaction: bool = False) -> Tuple[str, bool]:
        """Generate contextual response with advanced human-like conversation handling"""
        
        # Analyze conversation context for better response generation
        context_analysis = self.analyze_conversation_context(conversation_history, user_message)
        
        # Check if user is ready to buy
        is_ready = self.check_readiness_to_buy(conversation_history, user_message)
        
        # Generate appropriate response based on context
        if is_ready or context_analysis["intent"] == "purchase_intent":
            return self._generate_purchase_ready_response(user_message, product_info, context_analysis)
        elif is_first_interaction:
            return self._generate_welcome_response(user_message, product_info, context_analysis)
        elif context_analysis["intent"] == "conversation_summary":
            return self._generate_conversation_summary_response(conversation_history, product_info, context_analysis)
        elif context_analysis["is_off_topic"] or context_analysis["intent"] == "off_topic":
            return self._generate_off_topic_response(user_message, conversation_history, product_info, context_analysis)
        elif context_analysis["intent"] == "general_chat":
            return self._generate_general_chat_response(user_message, conversation_history, product_info, context_analysis)
        else:
            return self._generate_product_focused_response(user_message, conversation_history, product_info, context_analysis)

    def _generate_welcome_response(self, user_message: str, product_info: str, context: Dict) -> Tuple[str, bool]:
        """Generate warm welcome response for first interaction"""
        system_prompt = f"""You are Zara, a friendly and knowledgeable beauty consultant at our premium personal care store. This is your first interaction with this customer.

        PERSONALITY TRAITS:
        - Warm, approachable, and genuinely helpful
        - Enthusiastic about beauty and personal care
        - Professional yet conversational
        - Has a subtle sense of humor
        - Genuinely cares about finding the right products for customers

        BUSINESS CONTEXT: {self.business_context}

        RESPONSE GUIDELINES:
        1. Give a warm, personalized welcome
        2. Acknowledge what they're asking about specifically
        3. Show expertise and enthusiasm
        4. Ask relevant follow-up questions to understand their needs
        5. Keep it conversational, not salesy
        6. Use their message content to personalize your response

        Available products for context: {product_info}"""

        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"""Customer's first message: "{user_message}"
                
                Give them a warm welcome that acknowledges what they're looking for. Be enthusiastic but not overwhelming. Ask a thoughtful follow-up question to better understand their needs."""
            }
        ]

        return self._make_api_call(messages, temperature=0.8, max_tokens=180)

    def _generate_conversation_summary_response(self, conversation_history: str, product_info: str, context: Dict) -> Tuple[str, bool]:
        """Enhanced conversation summary with specific context recall"""
        previously_discussed = context.get("previously_discussed_products", [])
        conversation_topic = context.get("conversation_topic", "beauty products")
        
        system_prompt = f"""You are Zara, a friendly beauty consultant. The customer is asking what you've been discussing.

        IMPORTANT: Give them a SPECIFIC recap of your actual conversation, not a generic product list!

        RESPONSE STYLE:
        - Be natural and conversational, like a friend recapping a real chat
        - Mention the SPECIFIC products or topics you actually discussed
        - Reference the actual flow of your conversation
        - Show you remember the details of what they asked
        - Use phrases like "we were talking about..." or "you mentioned..."
        - If no specific products were discussed yet, be honest about that
        - Transition naturally to helping them continue

        BUSINESS CONTEXT: {self.business_context}"""

        products_context = ""
        if previously_discussed:
            products_context = f"Specific products mentioned: {', '.join(previously_discussed)}"
        else:
            products_context = "No specific products have been discussed in detail yet"

        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"""Here's our actual conversation so far:
                {conversation_history}
                
                {products_context}
                Conversation topic: {conversation_topic}
                Available products to reference: {product_info}
                
                The customer is asking about what you've been discussing. Give them a specific, accurate recap of YOUR ACTUAL conversation, not a generic product list. Be like a human who actually remembers the conversation details."""
            }
        ]

        return self._make_api_call(messages, temperature=0.6, max_tokens=200)

    def _generate_off_topic_response(self, user_message: str, conversation_history: str, product_info: str, context: Dict) -> Tuple[str, bool]:
        """Enhanced off-topic handling with natural human-like responses"""
        sentiment = context.get("user_sentiment", "neutral")
        previously_discussed = context.get("previously_discussed_products", [])
        
        system_prompt = f"""You are Zara, a friendly beauty consultant with excellent social skills and emotional intelligence. The customer just shared something unrelated to beauty products.

        CRITICAL RESPONSE STRATEGY:
        1. ACKNOWLEDGE what they said with genuine interest and appropriate emotion
        2. Respond like a real person would (congratulate, empathize, show interest, etc.)
        3. Find a NATURAL bridge to beauty/personal care (don't force it immediately)
        4. If you were discussing products before, reference that smoothly
        5. Keep it conversational and authentic

        EXAMPLES OF NATURAL RESPONSES:
        - Weather: "Oh that's nice/terrible! Weather definitely affects how our skin feels..."
        - Work: "That sounds great! It's always nice when work goes well. Speaking of feeling good..."
        - Personal news: "That's wonderful/I'm sorry to hear that! You know what might help you feel even better..."

        TONE MATCHING:
        - If they're excited → be excited with them first
        - If they're casual → be casual back
        - If they seem down → show empathy
        - Then naturally transition with care

        PREVIOUSLY DISCUSSED: {', '.join(previously_discussed) if previously_discussed else 'No specific products yet'}

        BUSINESS CONTEXT: {self.business_context}"""

        redirect_context = ""
        if previously_discussed:
            redirect_context = f"Earlier conversation included: {', '.join(previously_discussed)}"

        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"""Customer just said: "{user_message}"
                
                Previous conversation context: {conversation_history}
                {redirect_context}
                Available products: {product_info}
                Customer's current sentiment: {sentiment}
                
                Respond like a real human would to what they shared, then find a natural way to connect it back to beauty/personal care. Don't ignore what they said or immediately jump to sales talk. Be genuine and conversational."""
            }
        ]

        return self._make_api_call(messages, temperature=0.8, max_tokens=200)

    def _generate_general_chat_response(self, user_message: str, conversation_history: str, product_info: str, context: Dict) -> Tuple[str, bool]:
        """Handle general chat that can be redirected to products"""
        system_prompt = f"""You are Zara, a friendly beauty consultant. The customer is having a casual conversation that you can naturally connect to beauty or personal care.

        RESPONSE APPROACH:
        - Engage with their casual comment naturally
        - Find a creative way to connect it to beauty/personal care
        - Share relevant expertise or tips
        - Suggest products that might be relevant
        - Keep the conversation flowing smoothly

        BUSINESS CONTEXT: {self.business_context}"""

        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"""Customer said: "{user_message}"
                
                Conversation history: {conversation_history}
                Available products: {product_info}
                
                Engage with their message and smoothly connect it to beauty or personal care products."""
            }
        ]

        return self._make_api_call(messages, temperature=0.8, max_tokens=180)

    def _generate_product_focused_response(self, user_message: str, conversation_history: str, product_info: str, context: Dict) -> Tuple[str, bool]:
        """Enhanced product-focused response with better context awareness"""
        stage = context.get("conversation_stage", "exploration")
        sentiment = context.get("user_sentiment", "neutral")
        previously_discussed = context.get("previously_discussed_products", [])
        
        system_prompt = f"""You are Zara, an expert beauty consultant with years of experience and genuine passion for helping people look and feel their best. You understand beauty is personal and take time to understand each customer's unique needs.

        CUSTOMER CONTEXT:
        - Conversation stage: {stage}
        - Current sentiment: {sentiment}
        - Previously discussed: {', '.join(previously_discussed) if previously_discussed else 'Starting fresh'}
        - Intent: Product-focused discussion

        ENHANCED RESPONSE GUIDELINES by stage:
        - Exploration: Ask thoughtful questions, listen actively, suggest options based on their input
        - Consideration: Provide detailed info, compare options, address specific features they care about
        - Objection handling: Listen to concerns, empathize, offer solutions or alternatives
        - Ready to buy: Guide confidently but let them lead the pace

        CONVERSATION PRINCIPLES:
        - Reference what you've already discussed together
        - Build on their previous responses and preferences
        - Ask follow-up questions that show you're listening
        - Match their communication style and energy level
        - Provide expert advice without overwhelming them
        - Keep track of what they've liked or dismissed

        PERSONALITY TRAITS:
        - Genuinely helpful, not just sales-focused
        - Enthusiastic but respectful of their pace
        - Uses light humor when appropriate
        - Shows expertise through practical advice
        - Remembers customer preferences and builds on them

        BUSINESS CONTEXT: {self.business_context}"""

        conversation_context = ""
        if previously_discussed:
            conversation_context = f"Building on previous discussion about: {', '.join(previously_discussed)}"

        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"""Full conversation context: {conversation_history}
                Latest customer message: "{user_message}"
                {conversation_context}
                Available products to recommend: {product_info}
                
                Generate an expert response that:
                1. References and builds on your previous conversation
                2. Addresses their current message thoughtfully
                3. Moves the conversation forward naturally for the {stage} stage
                4. Shows you're listening and remembering their preferences
                5. Provides valuable expertise without being pushy"""
            }
        ]

        return self._make_api_call(messages, temperature=0.7, max_tokens=220)

    def _generate_purchase_ready_response(self, user_message: str, product_info: str, context: Dict) -> Tuple[str, bool]:
        """Generate response when customer is ready to purchase"""
        system_prompt = f"""You are Zara, a beauty consultant. The customer is showing strong purchase intent!

        RESPONSE APPROACH:
        - Acknowledge their decision enthusiastically
        - Confirm the product they're interested in
        - Provide helpful next steps
        - Maintain excitement and support
        - Be ready to hand over to the purchase process

        BUSINESS CONTEXT: {self.business_context}"""

        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"""Customer message: "{user_message}"
                Available products: {product_info}
                
                The customer is ready to buy! Generate an enthusiastic response that confirms their choice and guides them toward completing the purchase."""
            }
        ]

        return self._make_api_call(messages, temperature=0.6, max_tokens=150, is_ready=True)

    def _make_api_call(self, messages: List[Dict], temperature: float = 0.7, max_tokens: int = 200, is_ready: bool = False) -> Tuple[str, bool]:
        """Make API call with error handling"""
        if not self.client:
            fallback_responses = [
                "That's interesting! I'd love to help you find the perfect beauty products for your needs. What are you most interested in?",
                "I appreciate you sharing that with me! Speaking of taking care of yourself, have you been looking for any particular beauty or personal care products?",
                "Thanks for letting me know! Now, is there anything specific you'd like to explore in our beauty collection?"
            ]
            return fallback_responses[0], is_ready

        try:
            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            
            response_text = response.choices[0].message.content.strip()
            return response_text, is_ready
            
        except Exception as e:
            print(f"Error generating response: {e}")
            fallback_response = "I'd be happy to help you find what you're looking for. Could you tell me more about what interests you?"
            return fallback_response, False

ai_service = AIService()
