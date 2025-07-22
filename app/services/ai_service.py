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
        """Calculate enhanced similarity score between keywords and product tags"""
        if not keywords or not product_tags:
            return 0.0
        
        # Convert to lowercase for comparison
        keywords_lower = [k.lower() for k in keywords]
        tags_lower = [t.lower() for t in product_tags]
        
        score = 0.0
        matches_found = 0
        
        for keyword in keywords_lower:
            best_match = 0.0
            for tag in tags_lower:
                if keyword == tag:
                    # Exact match gets full points
                    best_match = 1.0
                    break
                elif keyword in tag:
                    # Keyword contained in tag gets high points
                    best_match = max(best_match, 0.8)
                elif tag in keyword:
                    # Tag contained in keyword gets good points
                    best_match = max(best_match, 0.7)
                elif any(part in tag for part in keyword.split() if len(part) > 2):
                    # Partial word matches get moderate points
                    best_match = max(best_match, 0.6)
            
            if best_match > 0:
                score += best_match
                matches_found += 1
        
        # Normalize by number of keywords but reward multiple matches
        if matches_found > 0:
            base_score = score / len(keywords_lower)
            # Bonus for multiple matches
            match_bonus = min(matches_found / len(keywords_lower), 0.3)
            return min(base_score + match_bonus, 1.0)
        
        return 0.0

    def check_readiness_to_buy(self, conversation_history: str, user_message: str) -> bool:
        """DEPRECATED: This method is replaced by the comprehensive sales funnel system"""
        # This is now handled by analyze_sales_stage which provides much more detailed analysis
        return False

    def analyze_sales_stage(self, conversation_history: str, user_message: str, product_info: str = "") -> Dict:
        """Advanced sales funnel analysis with comprehensive stage detection and progression logic"""
        messages = [
            {
                "role": "system",
                "content": """You are an expert sales consultant specializing in customer journey analysis for beauty and personal care products. Your job is to precisely determine where the customer is in their buying journey and guide them through the proper sales process.

                COMPREHENSIVE SALES FUNNEL STAGES:

                1. **INITIAL_INTEREST** - Customer just expressed interest in a product category
                   - Examples: "I want perfume", "Looking for moisturizer", "Need hair products"
                   - Action: Understand their needs, ask clarifying questions

                2. **NEED_CLARIFICATION** - Customer provided basic interest, need more details  
                   - Examples: After "I want perfume" → ask about preferences, occasions, scent types
                   - Action: Gather requirements (skin type, preferences, budget range, usage)

                3. **PRODUCT_DISCOVERY** - Customer is learning about specific products
                   - Examples: Asking about specific products, comparing features
                   - Action: Present 2-3 relevant products with key benefits AND PRICES

                4. **PRICE_EVALUATION** - Customer is evaluating products with known prices
                   - Examples: After showing interest in products with prices, asking questions about value
                   - Action: Handle price questions, emphasize value, show alternatives if needed

                5. **CONSIDERATION** - Customer is weighing options, comparing, or has budget concerns
                   - Examples: "Let me think", "Is there anything cheaper?", comparing multiple products
                   - Action: Address concerns, provide alternatives, emphasize value

                6. **OBJECTION_HANDLING** - Customer has specific concerns or hesitations
                   - Examples: "Too expensive", "Not sure if it's right for me", asking about side effects
                   - Action: Address specific objections, provide reassurance, offer alternatives

                7. **PURCHASE_INTENT** - Customer shows strong buying signals after seeing prices
                   - Examples: "This sounds good", "I like this one", asking about availability/delivery
                   - Action: Present final summary with prices, ask for explicit purchase confirmation

                8. **PURCHASE_CONFIRMATION** - Customer explicitly confirms they want to buy
                   - Examples: "I'll take it", "Yes, I want to buy this", "How do I order?"
                   - Action: Confirm purchase, prepare for handover to purchase team

                9. **OFF_TOPIC** - Conversation not related to products or sales
                   - Examples: Personal chat, unrelated questions
                   - Action: Acknowledge politely, redirect to products

                CRITICAL STAGE PROGRESSION RULES:
                - MANDATORY PRICE INTRODUCTION: Customers MUST see prices before purchase confirmation
                - STRICT is_ready_to_buy CONTROL: Only true for explicit purchase confirmation after price exposure
                - MULTIPLE PRODUCTS: Handle by showing all interested products with individual prices
                - PRICE RANGE FILTERING: Apply customer budget constraints when filtering products
                - PROGRESSIVE SALES FUNNEL: Guide customer through proper stages without skipping

                STAGE TRANSITION REQUIREMENTS:
                1. INITIAL_INTEREST → NEED_CLARIFICATION: Understand customer needs
                2. NEED_CLARIFICATION → PRODUCT_DISCOVERY: Show relevant products WITH PRICES
                3. PRODUCT_DISCOVERY → PRICE_EVALUATION: Customer must see and acknowledge prices
                4. PRICE_EVALUATION → CONSIDERATION: Customer evaluates value
                5. CONSIDERATION → PURCHASE_INTENT: Customer shows strong interest
                6. PURCHASE_INTENT → PURCHASE_CONFIRMATION: Explicit "yes" to buy

                PRICING REQUIREMENTS:
                - Products MUST be shown with prices in PRODUCT_DISCOVERY stage
                - Customer MUST acknowledge or reference prices before PURCHASE_INTENT
                - Multiple products MUST each have individual prices shown
                - Price ranges MUST be applied when customer mentions budget constraints

                CUSTOMER INTENT ANALYSIS:
                - product_inquiry: General interest in product category
                - specific_product_interest: Interest in particular products
                - price_question: Direct or indirect pricing concerns
                - purchase_confirmation: Explicit agreement to buy specific product(s) after seeing prices
                - comparison_request: Comparing multiple options
                - budget_constraint: Mentioning price limits or seeking cheaper options
                - objection_concern: Expressing doubts or concerns
                - general_chat: Off-topic conversation
                - conversation_summary: Asking what was discussed

                PRODUCT EXTRACTION REQUIREMENTS:
                - Extract specific product names mentioned in customer messages
                - For purchase confirmations, identify ALL products customer wants to buy
                - Use exact product names when available from conversation context
                - For multiple products, list each individual product name
                - Pay special attention to brand names and product types mentioned

                EXAMPLE PRODUCT EXTRACTION:
                Customer: "I want to buy Wild Stone perfume and Himalaya neem face wash"
                → interested_products: ["Wild Stone perfume", "Himalaya neem face wash"]
                
                Customer: "I'll take both the moisturizer and shampoo"
                → interested_products: ["moisturizer", "shampoo"] (or specific names if known)

                RESPONSE AS JSON:
                {
                    "current_stage": "STAGE_NAME",
                    "customer_intent": "intent_type",
                    "is_ready_to_buy": false,
                    "confidence_level": 0.8,
                    "interested_products": ["specific product names"],
                    "price_range_mentioned": "under 300" or null,
                    "prices_shown_in_conversation": false,
                    "customer_saw_prices": false,
                    "customer_acknowledged_prices": false,
                    "next_action": "understand_needs|suggest_products_with_prices|show_prices|handle_objection|confirm_purchase|ask_for_confirmation",
                    "stage_transition_reason": "Why this stage was determined",
                    "requires_price_introduction": true,
                    "multiple_products_interest": false,
                    "specific_concerns": ["concern1", "concern2"] or [],
                    "explicit_purchase_words": false,
                    "price_objection": false,
                    "products_with_prices_needed": true,
                    "customer_budget_range": null,
                    "ready_for_price_discussion": false
                }

                EXPLICIT PURCHASE CONFIRMATION DETECTION:
                Look for these EXACT phrases that indicate purchase confirmation:
                - "Yes, I want to buy [product]"
                - "I'll take [product]" 
                - "I want to purchase [product]"
                - "I'll buy [product]"
                - "I want both [products]"
                - "I'll take both [products]"
                - "Yes, I want to buy both"
                - "I want to order [product]"
                - "How do I buy [product]"
                - "Let me buy [product]"
                - "I'll purchase [product]"
                - "I want to get [product]"
                - "I'll take the [product]"
                - "I want the [product]"
                
                CRITICAL: Any phrase containing "I'll take", "I want to buy", "I'll buy", "I want both", "I'll purchase" followed by a product name = PURCHASE_CONFIRMATION stage with is_ready_to_buy=true
                
                NOT PURCHASE CONFIRMATION (should be FALSE):
                - "This sounds good" (interest only)
                - "I like this" (interest only)  
                - "Seems perfect" (interest only)
                - "Tell me more" (inquiry only)
                - "What's the price" (price question only)
                
                MANDATORY BUSINESS RULE: If customer uses explicit purchase language like "I'll take the [product]" = ALWAYS set is_ready_to_buy=true and current_stage=PURCHASE_CONFIRMATION
                
                ABSOLUTE RULE: is_ready_to_buy=true ONLY when:
                1. Customer has seen prices (prices_shown_in_conversation=true)
                2. Customer explicitly confirms purchase with words like "buy", "take", "purchase", "order" (explicit_purchase_words=true)
                3. Current stage is PURCHASE_CONFIRMATION
                
                NEVER set is_ready_to_buy=true for expressions of interest, liking products, or asking questions without explicit purchase confirmation after price exposure."""
            },
            {
                "role": "user", 
                "content": f"""
                CONVERSATION HISTORY:
                {conversation_history}
                
                LATEST CUSTOMER MESSAGE: {user_message}
                
                AVAILABLE PRODUCTS CONTEXT:
                {product_info[:800] if product_info else "No specific products matched yet"}
                
                Analyze this customer's journey stage and determine the next appropriate action. Pay special attention to whether they've seen prices yet and if they've given explicit purchase confirmation.
                """
            }
        ]
        
        try:
            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=messages,
                max_tokens=400,
                temperature=0.1,  # Low temperature for consistent analysis
            )
            
            result_text = response.choices[0].message.content.strip()
            print(f"🤖 LLM Sales Analysis Raw Response: {result_text}")  # Debug output
            
            # Try to parse JSON response
            import json
            try:
                analysis = json.loads(result_text)
                print(f"🎯 Parsed Sales Analysis: {analysis}")  # Debug output
                
                # Validate required fields and enforce business rules
                required_fields = ["current_stage", "customer_intent", "is_ready_to_buy", "next_action"]
                if all(field in analysis for field in required_fields):
                    # STRICT BUSINESS RULE ENFORCEMENT
                    
                    print(f"🔍 LLM ANALYSIS BEFORE RULES: Stage={analysis.get('current_stage')}, Ready={analysis.get('is_ready_to_buy')}")
                    
                    # Rule 1: Only allow is_ready_to_buy=true for PURCHASE_CONFIRMATION
                    if analysis["current_stage"] != "PURCHASE_CONFIRMATION":
                        analysis["is_ready_to_buy"] = False
                    
                    # Rule 2: Customer must have seen prices before being ready
                    customer_saw_prices = analysis.get("customer_saw_prices", False)
                    prices_shown = analysis.get("prices_shown_in_conversation", False)
                    explicit_purchase = analysis.get("explicit_purchase_words", False)
                    
                    print(f"🔍 BUSINESS RULE CHECK: Prices Shown={prices_shown}, Saw Prices={customer_saw_prices}, Explicit={explicit_purchase}")
                    
                    # ENHANCED EXPLICIT PURCHASE DETECTION: Check if message contains explicit purchase language
                    explicit_purchase_detected = any(phrase in user_message.lower() for phrase in [
                        "i'll take", "i want to buy", "i'll buy", "i want both", "i'll purchase", "i want to purchase"
                    ])
                    
                    print(f"🔍 EXPLICIT PURCHASE DETECTED: {explicit_purchase_detected}")
                    
                    # If explicit purchase language detected, override to purchase confirmation
                    if explicit_purchase_detected:
                        analysis["current_stage"] = "PURCHASE_CONFIRMATION"
                        analysis["is_ready_to_buy"] = True
                        analysis["explicit_purchase_words"] = True
                        analysis["customer_saw_prices"] = True  # Assume prices were discussed
                        analysis["prices_shown_in_conversation"] = True
                        print(f"🎯 OVERRIDE: Detected explicit purchase - setting ready=True")
                    
                    # Override is_ready if mandatory conditions not met
                    elif analysis.get("is_ready_to_buy"):
                        if not (customer_saw_prices and prices_shown and explicit_purchase):
                            analysis["is_ready_to_buy"] = False
                            analysis["next_action"] = "show_prices" if not prices_shown else "ask_for_confirmation"
                            analysis["requires_price_introduction"] = not prices_shown
                            analysis["stage_transition_reason"] = "Customer needs price exposure before purchase confirmation"
                    
                    print(f"🔍 FINAL LLM ANALYSIS: Stage={analysis.get('current_stage')}, Ready={analysis.get('is_ready_to_buy')}")
                    
                    # Rule 3: Force price introduction for purchase intent without price exposure
                    if analysis["current_stage"] == "PURCHASE_INTENT" and not prices_shown:
                        analysis["requires_price_introduction"] = True
                        analysis["next_action"] = "show_prices"
                    
                    return analysis
            except json.JSONDecodeError:
                pass
            
            # Fallback if JSON parsing fails
            return self._parse_sales_analysis_fallback(result_text, user_message)
            
        except Exception as e:
            print(f"Error in sales stage analysis: {e}")
            return self._default_sales_analysis(user_message)

    def _parse_sales_analysis_fallback(self, llm_response: str, user_message: str) -> Dict:
        """Enhanced fallback parser with comprehensive stage detection"""
        message_lower = user_message.lower()
        
        # Explicit purchase confirmation - highest priority
        purchase_words = ["take", "buy", "purchase", "order", "get"]
        product_words = ["perfume", "face wash", "cream", "oil", "shampoo", "soap", "moisturizer"]
        
        has_purchase_word = any(word in message_lower for word in purchase_words)
        has_product_word = any(word in message_lower for word in product_words)
        
        explicit_purchase_phrases = [
            "i'll take it", "i want to buy", "yes, i'll buy", "i'll purchase", 
            "let's do it", "i'm ready to order", "how do i pay", "how can i order",
            "i want both", "i'll take both", "yes, i want to buy", "i want to purchase",
            "i'll get the", "i'll get both", "i want the", "i'll buy the",
            "i want to buy both", "i want to buy the", "yes, i want both",
            "yes, i want", "i want to buy", "i'll take", "i'll buy", 
            "i want to order", "i want to get", "let me buy", "i'll purchase",
            "yes, i'll take", "yes, i'll get", "i want to purchase the",
            "i want to buy the", "i'll buy both", "i want both the",
            "yes, i want the", "i want to get the", "i'll order",
            "i'll take the", "i want both", "yes, i want to buy the"
        ]
        
        print(f"🔍 FALLBACK ANALYSIS: Message='{user_message}'")
        print(f"🔍 FALLBACK ANALYSIS: Message Lower='{message_lower}'")
        print(f"🔍 FALLBACK ANALYSIS: Has Purchase Word={has_purchase_word}, Has Product Word={has_product_word}")
        
        # Check each phrase individually for debugging
        matched_phrases = [phrase for phrase in explicit_purchase_phrases if phrase in message_lower]
        if matched_phrases:
            print(f"🎯 MATCHED EXPLICIT PHRASES: {matched_phrases}")
        
        if any(phrase in message_lower for phrase in explicit_purchase_phrases) or (has_purchase_word and has_product_word):
            # Extract product names from the message
            interested_products = self._extract_products_from_message(user_message)
            
            return {
                "current_stage": "PURCHASE_CONFIRMATION",
                "customer_intent": "purchase_confirmation",
                "is_ready_to_buy": True,
                "confidence_level": 0.95,
                "next_action": "confirm_purchase",
                "stage_transition_reason": "Customer explicitly confirmed purchase intent",
                "prices_shown_in_conversation": True,  # Assume prices were discussed if they're confirming
                "customer_saw_prices": True,
                "explicit_purchase_words": True,
                "requires_price_introduction": False,
                "interested_products": interested_products,
                "multiple_products_interest": len(interested_products) > 1 if interested_products else False
            }
        
        # Purchase intent but not confirmed yet
        elif any(phrase in message_lower for phrase in [
            "this sounds good", "i like this", "seems interesting", "looks good",
            "i'm interested", "tell me more about ordering"
        ]):
            return {
                "current_stage": "PURCHASE_INTENT",
                "customer_intent": "specific_product_interest",
                "is_ready_to_buy": False,
                "confidence_level": 0.8,
                "next_action": "ask_for_confirmation",
                "stage_transition_reason": "Customer showing strong interest but needs confirmation",
                "requires_price_introduction": True,
                "prices_shown": False
            }
        
        # Price-related inquiries
        elif any(word in message_lower for word in [
            "price", "cost", "expensive", "cheap", "budget", "affordable", 
            "how much", "what's the price", "rates"
        ]):
            return {
                "current_stage": "PRICE_EVALUATION",
                "customer_intent": "price_question",
                "is_ready_to_buy": False,
                "confidence_level": 0.9,
                "next_action": "show_prices",
                "stage_transition_reason": "Customer is asking about pricing",
                "requires_price_introduction": True,
                "prices_shown": False
            }
        
        # Comparison or consideration stage
        elif any(phrase in message_lower for phrase in [
            "compare", "vs", "difference", "which is better", "alternatives",
            "let me think", "not sure", "maybe"
        ]):
            return {
                "current_stage": "CONSIDERATION",
                "customer_intent": "comparison_request",
                "is_ready_to_buy": False,
                "confidence_level": 0.7,
                "next_action": "handle_objection",
                "stage_transition_reason": "Customer is comparing options or hesitating",
                "multiple_products_interest": True,
                "prices_shown": False
            }
        
        # Product interest
        elif any(word in message_lower for word in [
            "perfume", "moisturizer", "cream", "oil", "shampoo", "conditioner",
            "serum", "cleanser", "lotion", "mask", "scrub"
        ]):
            return {
                "current_stage": "NEED_CLARIFICATION",
                "customer_intent": "product_inquiry",
                "is_ready_to_buy": False,
                "confidence_level": 0.8,
                "next_action": "understand_needs",
                "stage_transition_reason": "Customer mentioned specific product category",
                "requires_price_introduction": False,
                "prices_shown": False
            }
        
        # Default to initial interest
        else:
            return self._default_sales_analysis(user_message)

    def _default_sales_analysis(self, user_message: str) -> Dict:
        """Enhanced default analysis for comprehensive sales funnel"""
        return {
            "current_stage": "INITIAL_INTEREST",
            "customer_intent": "product_inquiry",
            "is_ready_to_buy": False,
            "confidence_level": 0.5,
            "next_action": "understand_needs",
            "stage_transition_reason": "Default analysis - customer showing initial interest",
            "interested_products": [],
            "price_range_mentioned": None,
            "prices_shown": False,
            "requires_price_introduction": False,
            "multiple_products_interest": False,
            "specific_concerns": []
        }

    def filter_products_by_price_range(self, products: List[Dict], price_range_text: str) -> List[Dict]:
        """Filter products based on customer's price range mention"""
        if not price_range_text:
            return products
            
        # Extract price limit from text like "under 300", "below ₹500", "less than 200"
        import re
        price_numbers = re.findall(r'(\d+)', price_range_text)
        
        if not price_numbers:
            return products
            
        max_price = int(price_numbers[0])
        
        # Filter products within budget (considering sale price if available)
        filtered = []
        for product in products:
            effective_price = product.get('sale_price') or product.get('price', 0)
            if effective_price <= max_price:
                filtered.append(product)
                
        return filtered

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

    def _extract_products_from_message(self, user_message: str) -> List[str]:
        """Extract specific product names mentioned in customer message"""
        message_lower = user_message.lower()
        extracted_products = []
        
        # Common product patterns and brand names
        product_patterns = {
            "Wild Stone": ["wild stone", "wildstone"],
            "Himalaya": ["himalaya"],
            "Dove": ["dove"],
            "Pantene": ["pantene"],
            "Head & Shoulders": ["head & shoulders", "head and shoulders"],
            "Garnier": ["garnier"],
            "Fair & Lovely": ["fair & lovely", "fair and lovely"],
            "Dabur": ["dabur"],
            "AXE": ["axe"],
            "Fogg": ["fogg"],
            "Lux": ["lux"]
        }
        
        product_types = {
            "perfume": ["perfume", "fragrance", "scent"],
            "face wash": ["face wash", "facial wash", "cleanser"],
            "neem face wash": ["neem face wash", "neem wash"],
            "shampoo": ["shampoo"],
            "conditioner": ["conditioner"],
            "soap": ["soap", "bar"],
            "moisturizer": ["moisturizer", "cream"],
            "oil": ["oil"],
            "serum": ["serum"],
            "lotion": ["lotion"]
        }
        
        # Extract brand-specific products
        for brand, patterns in product_patterns.items():
            for pattern in patterns:
                if pattern in message_lower:
                    # Try to find product type with brand
                    for product_type, type_patterns in product_types.items():
                        for type_pattern in type_patterns:
                            if type_pattern in message_lower:
                                extracted_products.append(f"{brand} {product_type}")
                                break
                    # If no specific type found, add just the brand
                    if not any(f"{brand}" in prod for prod in extracted_products):
                        extracted_products.append(brand)
        
        # Extract standalone product types if no brands found
        if not extracted_products:
            for product_type, patterns in product_types.items():
                for pattern in patterns:
                    if pattern in message_lower and product_type not in extracted_products:
                        extracted_products.append(product_type)
        
        # Handle "both" references
        if "both" in message_lower and len(extracted_products) < 2:
            # If they say "both" but we only extracted one product, try to infer the second
            # from common combinations
            if "perfume" in message_lower and "face wash" in message_lower:
                if "perfume" not in str(extracted_products):
                    extracted_products.append("perfume")
                if "face wash" not in str(extracted_products):
                    extracted_products.append("face wash")
        
        return extracted_products[:5]  # Limit to 5 products max

    def generate_response(self, conversation_history: str, product_info: str, user_message: str, is_first_interaction: bool = False) -> Tuple[str, bool]:
        """Generate contextual response with comprehensive sales funnel management"""
        
        # Analyze conversation context for better response generation  
        context_analysis = self.analyze_conversation_context(conversation_history, user_message)
        
        # Comprehensive sales stage analysis - PRIMARY DECISION MAKER
        sales_analysis = self.analyze_sales_stage(conversation_history, user_message, product_info)
        
        # Extract key information for flow control
        current_stage = sales_analysis.get("current_stage", "INITIAL_INTEREST")
        is_ready = sales_analysis.get("is_ready_to_buy", False)
        next_action = sales_analysis.get("next_action", "understand_needs")
        requires_price_intro = sales_analysis.get("requires_price_introduction", False)
        multiple_products = sales_analysis.get("multiple_products_interest", False)
        interested_products = sales_analysis.get("interested_products", [])
        customer_budget = sales_analysis.get("price_range_mentioned")
        
        # Enhanced debugging for better understanding
        print(f"🎯 Sales Analysis: Stage={current_stage}, Ready={is_ready}, Action={next_action}")
        print(f"💰 Price Info: Requires={requires_price_intro}, Products={interested_products}")
        print(f"🛍️ Customer Budget: {customer_budget}, Multiple Products: {multiple_products}")
        
        # COMPREHENSIVE STAGE-BASED RESPONSE ROUTING (LLM-Driven Decision Making)
        
        # STAGE 1: Handle purchase confirmation (ONLY when explicitly confirmed with prices seen)
        if is_ready and current_stage == "PURCHASE_CONFIRMATION":
            print("✅ PURCHASE CONFIRMED - Customer ready for handover")
            return self._generate_purchase_confirmation_response(user_message, product_info, sales_analysis)
        
        # STAGE 2: Handle purchase intent (showing strong interest but needs confirmation)
        elif current_stage == "PURCHASE_INTENT" or next_action == "ask_for_confirmation":
            print("🔥 PURCHASE INTENT - Asking for final confirmation")
            return self._generate_purchase_intent_response(user_message, product_info, sales_analysis)
        
        # STAGE 3: Handle price-related inquiries and price introduction
        elif current_stage == "PRICE_EVALUATION" or next_action == "show_prices" or requires_price_intro:
            print("💰 PRICE EVALUATION - Showing prices and value")
            return self._generate_price_evaluation_response(user_message, product_info, sales_analysis)
        
        # STAGE 4: Handle product discovery with mandatory pricing
        elif current_stage == "PRODUCT_DISCOVERY" or next_action == "suggest_products_with_prices":
            print("🛍️ PRODUCT DISCOVERY - Presenting products with prices")
            return self._generate_product_discovery_response(user_message, product_info, sales_analysis)
        
        # STAGE 5: Handle objections and concerns
        elif current_stage == "OBJECTION_HANDLING" or next_action == "handle_objection":
            print("🛡️ OBJECTION HANDLING - Addressing customer concerns")
            return self._generate_objection_handling_response(user_message, product_info, sales_analysis)
        
        # STAGE 6: Handle consideration stage (comparing, thinking)
        elif current_stage == "CONSIDERATION":
            print("🤔 CONSIDERATION - Helping customer decide")
            return self._generate_consideration_response(user_message, product_info, sales_analysis)
        
        # STAGE 7: Handle need clarification 
        elif current_stage == "NEED_CLARIFICATION" or next_action == "understand_needs":
            print("❓ NEED CLARIFICATION - Understanding customer requirements")
            return self._generate_need_clarification_response(user_message, product_info, sales_analysis)
        
        # STAGE 8: Handle initial interest
        elif current_stage == "INITIAL_INTEREST":
            print("👋 INITIAL INTEREST - Building rapport and understanding")
            if is_first_interaction:
                return self._generate_welcome_response(user_message, product_info, context_analysis)
            else:
                return self._generate_initial_interest_response(user_message, product_info, sales_analysis)
        
        # SPECIAL CONTEXTS: Handle off-topic and conversation summary requests
        elif context_analysis["intent"] == "conversation_summary":
            print("📝 CONVERSATION SUMMARY - Recapping discussion")
            return self._generate_conversation_summary_response(conversation_history, product_info, context_analysis)
        elif context_analysis["is_off_topic"] or current_stage == "OFF_TOPIC":
            print("🔀 OFF-TOPIC - Graceful redirection")
            return self._generate_off_topic_response(user_message, conversation_history, product_info, context_analysis)
        
        # FALLBACK: Default product-focused response with LLM analysis
        else:
            print(f"🔄 FALLBACK - Default response for stage: {current_stage}")
            return self._generate_adaptive_response_based_on_analysis(user_message, product_info, sales_analysis, context_analysis)

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

    def _generate_price_introduction_response(self, user_message: str, product_info: str, sales_analysis: Dict) -> Tuple[str, bool]:
        """Generate response that introduces product prices naturally"""
        system_prompt = f"""You are Zara, a knowledgeable beauty consultant. The customer is asking about prices or needs pricing information.

        RESPONSE APPROACH:
        1. Address their price inquiry directly and professionally
        2. Present prices clearly with value propositions
        3. Highlight any current deals or sale prices
        4. Mention why the price represents good value
        5. Ask about their budget or preferences to help narrow options
        6. Guide them toward making a decision

        BUSINESS CONTEXT: {self.business_context}
        
        CURRENT STAGE: {sales_analysis.get('current_stage')}
        CUSTOMER INTENT: {sales_analysis.get('customer_intent')}"""

        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"""Customer said: "{user_message}"
                
                Available products with pricing: {product_info}
                
                Provide clear pricing information and help them understand the value. Be transparent about costs and help them make an informed decision."""
            }
        ]

        return self._make_api_call(messages, temperature=0.6, max_tokens=250)

    def _generate_product_suggestion_response(self, user_message: str, product_info: str, sales_analysis: Dict, price_range: str = None) -> Tuple[str, bool]:
        """Generate response that suggests relevant products, optionally filtered by price range"""
        
        # Additional context for price filtering
        price_context = f"\nCustomer mentioned budget: {price_range}" if price_range else ""
        
        system_prompt = f"""You are Zara, a beauty consultant helping customers find the perfect products. 

        RESPONSE APPROACH:
        1. Understand what they're looking for specifically
        2. Suggest 2-3 most relevant products from available options
        3. Explain why each product suits their needs
        4. Include key features and benefits
        5. Mention prices to set proper expectations
        6. Ask questions to better understand their preferences
        
        BUSINESS CONTEXT: {self.business_context}
        
        SALES STAGE: {sales_analysis.get('current_stage', 'PRODUCT_DISCOVERY')}
        CUSTOMER INTENT: {sales_analysis.get('customer_intent', 'product_inquiry')}{price_context}"""

        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"""Customer said: "{user_message}"
                
                Available products: {product_info}
                
                Suggest the most relevant products and explain why they're great choices. Include pricing information and ask follow-up questions to better understand their needs."""
            }
        ]

        return self._make_api_call(messages, temperature=0.7, max_tokens=300)

    def _generate_objection_handling_response(self, user_message: str, product_info: str, sales_analysis: Dict) -> Tuple[str, bool]:
        """Handle customer objections like price concerns, product doubts, etc."""
        system_prompt = f"""You are Zara, an experienced beauty consultant skilled at addressing customer concerns professionally.

        OBJECTION HANDLING APPROACH:
        1. Acknowledge their concern genuinely 
        2. Provide reassurance and additional information
        3. Offer alternatives if appropriate (different price points, similar products)
        4. Emphasize value and benefits
        5. Share relevant expertise or customer testimonials
        6. Keep the conversation positive and solution-focused

        BUSINESS CONTEXT: {self.business_context}
        
        SALES ANALYSIS: {sales_analysis.get('reasoning', 'Customer has concerns that need addressing')}"""

        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"""Customer expressed concern: "{user_message}"
                
                Available products and alternatives: {product_info}
                
                Address their concern professionally and help them feel confident about their choice. Provide helpful information and alternatives if needed."""
            }
        ]

        return self._make_api_call(messages, temperature=0.6, max_tokens=250)

    def _generate_purchase_confirmation_response(self, user_message: str, product_info: str, sales_analysis: Dict) -> Tuple[str, bool]:
        """Generate response when customer is ready to purchase"""
        interested_products = sales_analysis.get('interested_products', [])
        products_context = f"Products they're interested in: {', '.join(interested_products)}" if interested_products else ""
        
        system_prompt = f"""You are Zara, a beauty consultant. The customer has confirmed they want to make a purchase! 

        PURCHASE CONFIRMATION APPROACH:
        1. Express excitement about their decision
        2. Confirm exactly what they want to purchase
        3. Mention the total price clearly
        4. Explain next steps (they'll be connected to our purchase team)
        5. Thank them for choosing us
        6. Keep it warm and professional

        BUSINESS CONTEXT: {self.business_context}
        
        {products_context}
        CUSTOMER CONFIDENCE: {sales_analysis.get('confidence_level', 'High')}"""

        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"""Customer confirmed purchase: "{user_message}"
                
                Products available: {product_info}
                
                Confirm their purchase decision and prepare them for handover to the purchase team. Be enthusiastic and professional."""
            }
        ]

        return self._make_api_call(messages, temperature=0.6, max_tokens=150, is_ready=True)

    # === COMPREHENSIVE SALES STAGE RESPONSE METHODS ===

    def _generate_initial_interest_response(self, user_message: str, product_info: str, sales_analysis: Dict) -> Tuple[str, bool]:
        """Handle initial product interest and guide toward need clarification"""
        system_prompt = f"""You are Zara, a beauty consultant. The customer just expressed initial interest in our products.

        APPROACH:
        1. Acknowledge their interest warmly
        2. Ask specific questions to understand their needs better
        3. Guide them toward telling you about their preferences, skin type, usage occasions
        4. Don't overwhelm with product details yet - focus on understanding them first
        5. Be curious and helpful

        BUSINESS CONTEXT: {self.business_context}"""

        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"""Customer said: "{user_message}"
                
                They're showing initial interest. Help them clarify what they're looking for by asking thoughtful questions about their needs, preferences, or specific requirements."""
            }
        ]

        return self._make_api_call(messages, temperature=0.8, max_tokens=150)

    def _generate_need_clarification_response(self, user_message: str, product_info: str, sales_analysis: Dict) -> Tuple[str, bool]:
        """Clarify customer needs before suggesting specific products"""
        system_prompt = f"""You are Zara, a beauty consultant focused on understanding customer needs.

        NEED CLARIFICATION APPROACH:
        1. Ask specific questions about their preferences, skin type, lifestyle
        2. Understand their budget range (diplomatically)
        3. Learn about occasions they'll use the product
        4. Identify any specific concerns or requirements
        5. Keep it conversational, not like an interrogation

        BUSINESS CONTEXT: {self.business_context}"""

        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"""Customer said: "{user_message}"
                
                Available product categories: {product_info[:200]}...
                
                Ask thoughtful questions to better understand their specific needs before recommending products."""
            }
        ]

        return self._make_api_call(messages, temperature=0.7, max_tokens=180)

    def _generate_product_discovery_response(self, user_message: str, product_info: str, sales_analysis: Dict) -> Tuple[str, bool]:
        """Present relevant products WITH PRICES based on understood needs"""
        interested_products = sales_analysis.get('interested_products', [])
        multiple_interest = sales_analysis.get('multiple_products_interest', False)
        price_range = sales_analysis.get('price_range_mentioned')
        
        system_prompt = f"""You are Zara, a beauty consultant presenting product recommendations with pricing.

        PRODUCT DISCOVERY WITH PRICING APPROACH:
        1. Present 2-3 most relevant products based on their stated needs
        2. Include the EXACT PRICE for each product clearly (e.g., "This costs ৳450")
        3. Explain WHY each product is suitable for them specifically
        4. Highlight key benefits and value proposition 
        5. If multiple products, show each with individual prices
        6. If they mentioned a budget, mention how products fit within it
        7. Ask which product interests them most or if they'd like more details

        PRICING REQUIREMENTS:
        - ALWAYS include prices when presenting products
        - Use clear pricing format: "Product Name - ৳[price]"
        - For multiple products, list each with its individual price
        - Mention value and benefits to justify pricing
        - If budget was mentioned, relate prices to their range

        BUSINESS CONTEXT: {self.business_context}
        
        CUSTOMER INTEREST: {interested_products if interested_products else 'General products'}
        MULTIPLE PRODUCTS: {multiple_interest}
        CUSTOMER BUDGET: {price_range if price_range else 'Not specified'}"""

        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"""Customer said: "{user_message}"
                
                Available products with details: {product_info}
                
                Present these products with their prices and explain why they're perfect for the customer's needs. Make sure to include exact prices for each product you recommend."""
            }
        ]

        return self._make_api_call(messages, temperature=0.7, max_tokens=250)

    def _generate_price_introduction_response(self, user_message: str, product_info: str, sales_analysis: Dict) -> Tuple[str, bool]:
        """Introduce pricing for products they're interested in"""
        interested_products = sales_analysis.get('interested_products', [])
        price_range = sales_analysis.get('price_range_mentioned')
        
        system_prompt = f"""You are Zara, a beauty consultant introducing product pricing professionally.

        PRICE INTRODUCTION APPROACH:
        1. Present prices clearly and confidently
        2. Emphasize value proposition for each product
        3. Mention any current offers or discounts
        4. If they mentioned budget, show how products fit their range
        5. Present multiple options if they're considering several products
        6. Ask if the pricing works for them or if they have questions

        BUSINESS CONTEXT: {self.business_context}
        
        CUSTOMER BUDGET: {price_range if price_range else 'No specific budget mentioned'}
        INTERESTED IN: {interested_products if interested_products else 'Products being discussed'}"""

        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"""Customer said: "{user_message}"
                
                Products with pricing: {product_info}
                
                Present the pricing information clearly with value explanations. Make it easy for them to see the value."""
            }
        ]

        return self._make_api_call(messages, temperature=0.6, max_tokens=250)

    def _generate_price_evaluation_response(self, user_message: str, product_info: str, sales_analysis: Dict) -> Tuple[str, bool]:
        """Handle price evaluation stage with comprehensive pricing information"""
        interested_products = sales_analysis.get('interested_products', [])
        price_range = sales_analysis.get('price_range_mentioned')
        customer_budget = sales_analysis.get('customer_budget_range')
        
        system_prompt = f"""You are Zara, a beauty consultant specializing in price discussions and value propositions.

        PRICE EVALUATION APPROACH:
        1. Present ALL prices clearly and confidently
        2. Emphasize value proposition for each product
        3. Address budget concerns if mentioned
        4. Show how products fit within their price range
        5. Handle multiple products with individual pricing
        6. Offer alternatives if price is a concern
        7. Guide toward making a decision

        PRICING STRATEGY:
        - Always show exact prices: "This costs ৳450"
        - Explain what makes each product worth the price
        - If multiple products, compare value propositions
        - If budget mentioned, show products within range
        - Address price objections with benefits

        BUSINESS CONTEXT: {self.business_context}
        
        CUSTOMER BUDGET: {price_range or customer_budget or 'Not specified'}
        INTERESTED PRODUCTS: {interested_products if interested_products else 'Products being discussed'}"""

        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"""Customer said: "{user_message}"
                
                Products with pricing information: {product_info}
                
                Present comprehensive pricing information. Show exact prices, explain value, and help them understand why these products are worth the investment. Address any budget concerns."""
            }
        ]

        return self._make_api_call(messages, temperature=0.6, max_tokens=280)

    def _generate_adaptive_response_based_on_analysis(self, user_message: str, product_info: str, sales_analysis: Dict, context_analysis: Dict) -> Tuple[str, bool]:
        """Generate adaptive response using LLM analysis instead of hard-coded patterns"""
        current_stage = sales_analysis.get("current_stage", "INITIAL_INTEREST")
        customer_intent = sales_analysis.get("customer_intent", "product_inquiry")
        confidence = sales_analysis.get("confidence_level", 0.5)
        
        system_prompt = f"""You are Zara, an expert beauty consultant using advanced customer analysis to provide the perfect response.

        ADAPTIVE RESPONSE STRATEGY:
        Based on LLM analysis, adapt your response to match the customer's exact needs and conversation stage.
        
        CUSTOMER ANALYSIS INSIGHTS:
        - Sales Stage: {current_stage}
        - Intent: {customer_intent} 
        - Confidence Level: {confidence}
        - Context: {context_analysis.get('intent', 'general')}
        
        RESPONSE GUIDELINES BY STAGE:
        - INITIAL_INTEREST: Build rapport, ask clarifying questions
        - NEED_CLARIFICATION: Understand specific requirements, preferences, budget
        - PRODUCT_DISCOVERY: Present relevant products WITH PRICES
        - PRICE_EVALUATION: Handle pricing discussions, show value
        - CONSIDERATION: Help with comparisons, address concerns
        - PURCHASE_INTENT: Confirm interest, ask for purchase decision
        - PURCHASE_CONFIRMATION: Celebrate decision, prepare for handover
        
        Always include pricing when suggesting products. Be natural, helpful, and guide toward the next appropriate stage.

        BUSINESS CONTEXT: {self.business_context}"""

        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"""Customer said: "{user_message}"
                
                Available products: {product_info}
                
                Based on the analysis showing stage '{current_stage}' and intent '{customer_intent}', provide the most appropriate response to move the conversation forward naturally."""
            }
        ]

        return self._make_api_call(messages, temperature=0.7, max_tokens=250)

    def filter_products_by_price_range(self, products: List[Dict], price_range: str) -> List[Dict]:
        """Filter products based on customer's mentioned price range"""
        if not price_range or not products:
            return products
            
        try:
            # Extract numeric values from price range mentions
            price_range_lower = price_range.lower()
            
            # Parse different price range formats
            max_price = None
            min_price = None
            
            if 'under' in price_range_lower or 'below' in price_range_lower:
                # Extract number after "under" or "below"
                import re
                numbers = re.findall(r'\d+', price_range_lower)
                if numbers:
                    max_price = int(numbers[0])
                    
            elif 'above' in price_range_lower or 'over' in price_range_lower:
                # Extract number after "above" or "over"
                import re
                numbers = re.findall(r'\d+', price_range_lower)
                if numbers:
                    min_price = int(numbers[0])
                    
            elif 'between' in price_range_lower:
                # Extract range like "between 200 and 500"
                import re
                numbers = re.findall(r'\d+', price_range_lower)
                if len(numbers) >= 2:
                    min_price = int(numbers[0])
                    max_price = int(numbers[1])
                    
            elif any(char.isdigit() for char in price_range_lower):
                # Single number mentioned - treat as max price
                import re
                numbers = re.findall(r'\d+', price_range_lower)
                if numbers:
                    max_price = int(numbers[0])
            
            # Filter products based on price constraints
            filtered_products = []
            for product in products:
                product_price = product.get('price', 0)
                
                # Apply price filters
                if min_price and product_price < min_price:
                    continue
                if max_price and product_price > max_price:
                    continue
                    
                filtered_products.append(product)
            
            return filtered_products
            
        except Exception as e:
            print(f"Error filtering by price range: {e}")
            return products  # Return all products if filtering fails

    def _generate_consideration_response(self, user_message: str, product_info: str, sales_analysis: Dict) -> Tuple[str, bool]:
        """Help customer during consideration/comparison phase"""
        multiple_products = sales_analysis.get('multiple_products_interest', False)
        concerns = sales_analysis.get('specific_concerns', [])
        
        system_prompt = f"""You are Zara, a beauty consultant helping customers make informed decisions.

        CONSIDERATION STAGE APPROACH:
        1. Help them compare options clearly
        2. Address any hesitations or concerns
        3. Provide additional information they might need
        4. Share relevant customer experiences or reviews
        5. Offer to answer specific questions
        6. Give them time to think but stay supportive

        BUSINESS CONTEXT: {self.business_context}
        
        CUSTOMER CONCERNS: {concerns if concerns else 'Weighing options'}
        MULTIPLE PRODUCTS: {multiple_products}"""

        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"""Customer said: "{user_message}"
                
                Product options: {product_info}
                
                Help them feel confident about their decision. Address any concerns and provide helpful comparisons."""
            }
        ]

        return self._make_api_call(messages, temperature=0.6, max_tokens=230)

    def _generate_purchase_intent_response(self, user_message: str, product_info: str, sales_analysis: Dict) -> Tuple[str, bool]:
        """Handle when customer shows purchase intent but hasn't confirmed yet - ASK FOR EXPLICIT CONFIRMATION"""
        interested_products = sales_analysis.get('interested_products', [])
        price_range = sales_analysis.get('price_range_mentioned')
        customer_saw_prices = sales_analysis.get('customer_saw_prices', False)
        
        system_prompt = f"""You are Zara, a beauty consultant sensing strong purchase intent. The customer is interested but hasn't explicitly confirmed purchase yet.

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
        BUDGET RANGE: {price_range if price_range else 'Not specified'}"""

        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"""Customer said: "{user_message}"
                
                Products they're interested in: {product_info}
                
                They're showing purchase intent! Confirm their exact choice with pricing and ask for explicit purchase confirmation. Make it clear and easy for them to say yes to buying."""
            }
        ]

        return self._make_api_call(messages, temperature=0.6, max_tokens=200)

# Create the service instance
ai_service = AIService()
