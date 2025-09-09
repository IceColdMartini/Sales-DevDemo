"""
Enhanced Product Matcher
=======================

Improved product matching with better semantic understanding and efficiency.
Addresses the product matching issues identified in testing.
"""

import logging
import asyncio
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass
import re
from collections import defaultdict

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import BaseMessage
try:
    from langchain_core.output_parsers import PydanticOutputParser
except ImportError:
    from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

@dataclass
class ProductMatch:
    """Enhanced product match with confidence scoring."""
    product: Dict[str, Any]
    confidence_score: float
    match_reasons: List[str]
    match_type: str  # direct, semantic, category, brand
    relevance_keywords: List[str]

class ProductSearchRequest(BaseModel):
    """Enhanced product search request."""
    query_terms: List[str] = Field(description="Main search terms from customer message")
    skin_concerns: List[str] = Field(description="Identified skin concerns")
    product_categories: List[str] = Field(description="Product categories of interest")
    brand_preferences: List[str] = Field(description="Brand preferences if mentioned")
    price_range: Optional[str] = Field(description="Price range if specified")
    ingredient_preferences: List[str] = Field(description="Preferred or avoided ingredients")

class EnhancedProductMatcher:
    """
    Enhanced product matching with improved semantic understanding.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Enhanced keyword mappings
        self.category_keywords = {
            "cleanser": ["cleanser", "cleansing", "face wash", "foam", "gel", "micellar", "oil cleanser"],
            "moisturizer": ["moisturizer", "cream", "lotion", "hydrating", "hydration", "moisture"],
            "serum": ["serum", "essence", "treatment", "concentrate", "ampoule"],
            "sunscreen": ["sunscreen", "spf", "sun protection", "uv protection", "sunblock"],
            "toner": ["toner", "astringent", "facial water", "refreshing", "balancing"],
            "mask": ["mask", "masque", "sheet mask", "clay mask", "treatment mask"],
            "eye_cream": ["eye cream", "eye serum", "eye gel", "under eye", "eye care"],
            "exfoliant": ["exfoliant", "scrub", "peeling", "aha", "bha", "salicylic", "glycolic"],
            "oil": ["face oil", "facial oil", "oil", "argan", "jojoba", "rosehip"],
            "makeup": ["foundation", "concealer", "lipstick", "eyeshadow", "mascara", "blush"]
        }

        self.concern_keywords = {
            "acne": ["acne", "breakout", "pimple", "blemish", "blackhead", "whitehead", "oily"],
            "aging": ["aging", "anti-aging", "wrinkle", "fine lines", "mature skin", "firmness"],
            "dry_skin": ["dry", "dehydrated", "flaky", "tight", "rough", "parched"],
            "sensitive": ["sensitive", "irritated", "reactive", "gentle", "soothing", "calming"],
            "pigmentation": ["dark spots", "hyperpigmentation", "melasma", "uneven tone", "brightening"],
            "dullness": ["dull", "lackluster", "radiance", "glow", "brightening", "luminous"],
            "large_pores": ["pores", "enlarged pores", "minimizing", "refining", "smoothing"],
            "redness": ["redness", "rosacea", "inflammation", "irritation", "calming"]
        }

        self.ingredient_keywords = {
            "hyaluronic_acid": ["hyaluronic acid", "hyaluronic", "ha", "hydrating"],
            "vitamin_c": ["vitamin c", "ascorbic acid", "l-ascorbic", "brightening"],
            "retinol": ["retinol", "retinoid", "vitamin a", "tretinoin", "anti-aging"],
            "niacinamide": ["niacinamide", "vitamin b3", "nicotinamide", "pore refining"],
            "salicylic_acid": ["salicylic acid", "bha", "beta hydroxy", "acne treatment"],
            "glycolic_acid": ["glycolic acid", "aha", "alpha hydroxy", "exfoliating"],
            "peptides": ["peptides", "matrixyl", "argireline", "firming"],
            "ceramides": ["ceramides", "barrier repair", "moisture barrier"],
            "natural": ["natural", "organic", "plant-based", "botanical", "herbal"],
            "sulfate_free": ["sulfate-free", "sls-free", "gentle", "no sulfates"]
        }

        # Price range mappings
        self.price_ranges = {
            "budget": (0, 25),
            "affordable": (10, 50),
            "mid_range": (25, 100),
            "luxury": (75, 200),
            "premium": (150, 500)
        }

        # Initialize Azure OpenAI LLM for semantic understanding
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
                temperature=0.1,
                max_tokens=200
            )
        else:
            self.llm = None

        # Enhanced product search prompt
        self.search_prompt = ChatPromptTemplate.from_template("""
        You are an expert beauty product advisor. Analyze the customer's message to extract detailed product search information.

        Customer Message: "{message}"
        Conversation Context: {context}

        Extract the following information:

        QUERY TERMS: Main keywords that describe what the customer is looking for
        SKIN CONCERNS: Specific skin issues mentioned (acne, aging, dryness, sensitivity, etc.)
        PRODUCT CATEGORIES: Types of products they want (cleanser, serum, moisturizer, etc.)
        BRAND PREFERENCES: Any specific brands mentioned or preferred
        PRICE RANGE: Budget constraints if mentioned (budget/affordable/mid-range/luxury/premium)
        INGREDIENT PREFERENCES: Specific ingredients they want or want to avoid

        Examples:
        "I need a gentle cleanser for sensitive acne-prone skin under $30" →
        - Query Terms: ["gentle cleanser", "sensitive", "acne-prone"]  
        - Skin Concerns: ["sensitive", "acne"]
        - Product Categories: ["cleanser"]
        - Price Range: "budget"

        "Looking for anti-aging serums with retinol, preferably The Ordinary or Neutrogena" →
        - Query Terms: ["anti-aging serum", "retinol"]
        - Skin Concerns: ["aging"]  
        - Product Categories: ["serum"]
        - Brand Preferences: ["The Ordinary", "Neutrogena"]
        - Ingredient Preferences: ["retinol"]

        {format_instructions}
        """)

        self.search_parser = PydanticOutputParser(pydantic_object=ProductSearchRequest)

    async def find_matching_products(self, 
                                   message: str, 
                                   conversation_history: List[BaseMessage],
                                   available_products: List[Dict]) -> List[ProductMatch]:
        """
        Enhanced product matching with multiple strategies.
        """
        try:
            # Extract search requirements
            search_request = await self._extract_search_requirements(message, conversation_history)
            
            # Apply multiple matching strategies
            matches = []
            
            # 1. Direct keyword matching (fast, high precision)
            direct_matches = self._direct_keyword_matching(search_request, available_products)
            matches.extend(direct_matches)
            
            # 2. Category-based matching
            category_matches = self._category_based_matching(search_request, available_products)
            matches.extend(category_matches)
            
            # 3. Concern-based matching  
            concern_matches = self._concern_based_matching(search_request, available_products)
            matches.extend(concern_matches)
            
            # 4. Brand matching
            brand_matches = self._brand_matching(search_request, available_products)
            matches.extend(brand_matches)
            
            # 5. Ingredient matching
            ingredient_matches = self._ingredient_matching(search_request, available_products)
            matches.extend(ingredient_matches)
            
            # Deduplicate and rank matches
            final_matches = self._deduplicate_and_rank(matches, search_request)
            
            self.logger.info(f"🔍 Found {len(final_matches)} enhanced product matches")
            return final_matches[:10]  # Return top 10 matches
            
        except Exception as e:
            self.logger.error(f"❌ Enhanced product matching failed: {e}")
            return self._fallback_matching(message, available_products)

    async def _extract_search_requirements(self, message: str, conversation_history: List[BaseMessage]) -> ProductSearchRequest:
        """
        Extract detailed search requirements using LLM and rule-based analysis.
        """
        try:
            if self.llm:
                # Use LLM for sophisticated extraction
                context = self._format_conversation_context(conversation_history)
                
                chain = self.search_prompt | self.llm | self.search_parser
                
                search_request = await chain.ainvoke({
                    "message": message,
                    "context": context,
                    "format_instructions": self.search_parser.get_format_instructions()
                })
                
                self.logger.info(f"🎯 LLM extracted search: {len(search_request.query_terms)} terms, {len(search_request.skin_concerns)} concerns")
                return search_request
            else:
                # Fallback to rule-based extraction
                return self._rule_based_extraction(message)
                
        except Exception as e:
            self.logger.error(f"❌ Search extraction failed: {e}")
            return self._rule_based_extraction(message)

    def _rule_based_extraction(self, message: str) -> ProductSearchRequest:
        """
        Rule-based search requirement extraction.
        """
        message_lower = message.lower()
        
        # Extract query terms (simple tokenization)
        query_terms = []
        words = re.findall(r'\b\w+\b', message_lower)
        for i, word in enumerate(words):
            if word in ['need', 'want', 'looking', 'for'] and i < len(words) - 1:
                query_terms.extend(words[i+1:i+3])
        
        # Extract categories
        categories = []
        for category, keywords in self.category_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                categories.append(category)
        
        # Extract concerns
        concerns = []
        for concern, keywords in self.concern_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                concerns.append(concern)
        
        # Extract ingredients
        ingredients = []
        for ingredient, keywords in self.ingredient_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                ingredients.append(ingredient)
        
        # Extract brands (common beauty brands)
        brands = []
        common_brands = ["cetaphil", "neutrogena", "cerave", "olay", "l'oreal", "maybelline", 
                        "clinique", "estee lauder", "the ordinary", "paula's choice"]
        for brand in common_brands:
            if brand in message_lower:
                brands.append(brand)
        
        # Extract price range
        price_range = None
        if any(word in message_lower for word in ["budget", "cheap", "affordable", "under"]):
            price_range = "budget"
        elif any(word in message_lower for word in ["luxury", "premium", "high-end"]):
            price_range = "luxury"
        elif any(word in message_lower for word in ["mid-range", "moderate"]):
            price_range = "mid_range"
        
        return ProductSearchRequest(
            query_terms=query_terms or [message_lower[:20]],
            skin_concerns=concerns,
            product_categories=categories,
            brand_preferences=brands,
            price_range=price_range,
            ingredient_preferences=ingredients
        )

    def _direct_keyword_matching(self, search_request: ProductSearchRequest, products: List[Dict]) -> List[ProductMatch]:
        """
        Direct keyword matching against product names and descriptions.
        """
        matches = []
        
        for product in products:
            score = 0.0
            reasons = []
            keywords = []
            
            product_text = f"{product.get('name', '')} {product.get('description', '')} {product.get('category', '')}".lower()
            
            # Match query terms
            for term in search_request.query_terms:
                if term.lower() in product_text:
                    score += 0.3
                    reasons.append(f"Contains '{term}'")
                    keywords.append(term)
            
            if score > 0:
                matches.append(ProductMatch(
                    product=product,
                    confidence_score=min(score, 1.0),
                    match_reasons=reasons,
                    match_type="direct",
                    relevance_keywords=keywords
                ))
        
        return matches

    def _category_based_matching(self, search_request: ProductSearchRequest, products: List[Dict]) -> List[ProductMatch]:
        """
        Match products based on category requirements.
        """
        matches = []
        
        if not search_request.product_categories:
            return matches
        
        for product in products:
            score = 0.0
            reasons = []
            keywords = []
            
            product_category = product.get('category', '').lower()
            product_name = product.get('name', '').lower()
            
            for category in search_request.product_categories:
                category_words = self.category_keywords.get(category, [category])
                
                for keyword in category_words:
                    if keyword in product_category or keyword in product_name:
                        score += 0.4
                        reasons.append(f"Category match: {category}")
                        keywords.append(keyword)
                        break
            
            if score > 0:
                matches.append(ProductMatch(
                    product=product,
                    confidence_score=min(score, 1.0),
                    match_reasons=reasons,
                    match_type="category",
                    relevance_keywords=keywords
                ))
        
        return matches

    def _concern_based_matching(self, search_request: ProductSearchRequest, products: List[Dict]) -> List[ProductMatch]:
        """
        Match products based on skin concerns.
        """
        matches = []
        
        if not search_request.skin_concerns:
            return matches
        
        for product in products:
            score = 0.0
            reasons = []
            keywords = []
            
            product_text = f"{product.get('name', '')} {product.get('description', '')} {product.get('benefits', '')}".lower()
            
            for concern in search_request.skin_concerns:
                concern_words = self.concern_keywords.get(concern, [concern])
                
                for keyword in concern_words:
                    if keyword in product_text:
                        score += 0.35
                        reasons.append(f"Addresses {concern}")
                        keywords.append(keyword)
            
            if score > 0:
                matches.append(ProductMatch(
                    product=product,
                    confidence_score=min(score, 1.0),
                    match_reasons=reasons,
                    match_type="concern",
                    relevance_keywords=keywords
                ))
        
        return matches

    def _brand_matching(self, search_request: ProductSearchRequest, products: List[Dict]) -> List[ProductMatch]:
        """
        Match products based on brand preferences.
        """
        matches = []
        
        if not search_request.brand_preferences:
            return matches
        
        for product in products:
            product_brand = product.get('brand', '').lower()
            
            for preferred_brand in search_request.brand_preferences:
                if preferred_brand.lower() in product_brand:
                    matches.append(ProductMatch(
                        product=product,
                        confidence_score=0.8,  # High confidence for exact brand match
                        match_reasons=[f"Brand match: {preferred_brand}"],
                        match_type="brand",
                        relevance_keywords=[preferred_brand]
                    ))
        
        return matches

    def _ingredient_matching(self, search_request: ProductSearchRequest, products: List[Dict]) -> List[ProductMatch]:
        """
        Match products based on ingredient preferences.
        """
        matches = []
        
        if not search_request.ingredient_preferences:
            return matches
        
        for product in products:
            score = 0.0
            reasons = []
            keywords = []
            
            ingredient_text = f"{product.get('key_ingredients', '')} {product.get('description', '')}".lower()
            
            for ingredient in search_request.ingredient_preferences:
                ingredient_words = self.ingredient_keywords.get(ingredient, [ingredient])
                
                for keyword in ingredient_words:
                    if keyword in ingredient_text:
                        score += 0.4
                        reasons.append(f"Contains {ingredient}")
                        keywords.append(keyword)
            
            if score > 0:
                matches.append(ProductMatch(
                    product=product,
                    confidence_score=min(score, 1.0),
                    match_reasons=reasons,
                    match_type="ingredient",
                    relevance_keywords=keywords
                ))
        
        return matches

    def _deduplicate_and_rank(self, matches: List[ProductMatch], search_request: ProductSearchRequest) -> List[ProductMatch]:
        """
        Remove duplicates and rank matches by relevance.
        """
        # Group matches by product ID
        product_groups = defaultdict(list)
        for match in matches:
            product_id = match.product.get('id') or match.product.get('name')
            product_groups[product_id].append(match)
        
        # Combine scores for duplicate products
        final_matches = []
        for product_id, group in product_groups.items():
            if not group:
                continue
            
            # Use the first product as base
            base_match = group[0]
            
            # Combine confidence scores and reasons
            total_score = sum(match.confidence_score for match in group)
            all_reasons = []
            all_keywords = []
            match_types = set()
            
            for match in group:
                all_reasons.extend(match.match_reasons)
                all_keywords.extend(match.relevance_keywords)
                match_types.add(match.match_type)
            
            # Apply price range filter if specified
            if search_request.price_range:
                price_range = self.price_ranges.get(search_request.price_range)
                if price_range:
                    product_price = float(base_match.product.get('price', 0))
                    if not (price_range[0] <= product_price <= price_range[1]):
                        total_score *= 0.5  # Reduce score for price mismatch
            
            final_match = ProductMatch(
                product=base_match.product,
                confidence_score=min(total_score, 1.0),
                match_reasons=list(set(all_reasons)),
                match_type="/".join(sorted(match_types)),
                relevance_keywords=list(set(all_keywords))
            )
            
            final_matches.append(final_match)
        
        # Sort by confidence score (descending)
        final_matches.sort(key=lambda x: x.confidence_score, reverse=True)
        
        return final_matches

    def _fallback_matching(self, message: str, products: List[Dict]) -> List[ProductMatch]:
        """
        Simple fallback matching when enhanced methods fail.
        """
        matches = []
        message_lower = message.lower()
        
        for product in products:
            score = 0.0
            reasons = []
            
            product_text = f"{product.get('name', '')} {product.get('description', '')}".lower()
            
            # Simple word overlap
            message_words = set(re.findall(r'\w+', message_lower))
            product_words = set(re.findall(r'\w+', product_text))
            
            overlap = message_words.intersection(product_words)
            if overlap:
                score = len(overlap) / max(len(message_words), 1)
                reasons.append(f"Word overlap: {', '.join(list(overlap)[:3])}")
            
            if score > 0.1:
                matches.append(ProductMatch(
                    product=product,
                    confidence_score=score,
                    match_reasons=reasons,
                    match_type="fallback",
                    relevance_keywords=list(overlap)
                ))
        
        return sorted(matches, key=lambda x: x.confidence_score, reverse=True)[:5]

    def _format_conversation_context(self, conversation_history: List[BaseMessage]) -> str:
        """
        Format conversation context for LLM analysis.
        """
        if not conversation_history:
            return "No previous conversation"
        
        # Get last 3 messages for context
        recent = conversation_history[-3:]
        formatted = []
        
        for msg in recent:
            if hasattr(msg, 'type') and hasattr(msg, 'content'):
                role = "Customer" if msg.type == "human" else "Assistant"
                formatted.append(f"{role}: {msg.content[:80]}...")
        
        return "\n".join(formatted)

# Create enhanced product matcher instance
enhanced_product_matcher = EnhancedProductMatcher()
