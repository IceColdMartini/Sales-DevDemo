"""
Product Matcher
===============

Handles keyword extraction and sophisticated product matching using LangChain.
Enhanced with semantic similarity, fuzzy matching, and multi-criteria scoring.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
import re
import math
from dataclasses import dataclass
from collections import defaultdict
import asyncio

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import BaseMessage
try:
    from langchain_core.output_parsers import PydanticOutputParser
except ImportError:
    from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

from app.db.postgres_handler import postgres_handler
from . import ProductMatch

logger = logging.getLogger(__name__)

class KeywordExtraction(BaseModel):
    """Pydantic model for keyword extraction output."""
    keywords: List[str] = Field(description="Extracted keywords from user message")
    intent: str = Field(description="User's intent (buy, inquire, compare, etc.)")
    urgency: str = Field(description="Urgency level (high, medium, low)")
    price_range: Optional[Tuple[float, float]] = Field(description="Price range mentioned", default=None)
    preferences: List[str] = Field(description="User preferences (organic, vegan, etc.)", default_factory=list)

@dataclass
class EnhancedProductMatch:
    """Enhanced product match with detailed scoring"""
    product: Dict
    confidence_score: float
    reasoning: str
    match_factors: Dict[str, float]
    semantic_similarity: float
    tag_overlap: float
    price_match: float

class ProductMatcher:
    """
    Handles keyword extraction and sophisticated product matching.
    Enhanced with semantic similarity, fuzzy matching, and multi-criteria scoring.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

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
                temperature=0.3,
                max_tokens=1000
            )
        else:
            self.llm = None

        # Initialize keyword extraction chain
        self.keyword_extraction_prompt = ChatPromptTemplate.from_template(
            "You are an expert at extracting keywords and understanding user intent from beauty/cosmetics customer messages.\n\n"
            "Analyze the following customer message and extract:\n"
            "1. Keywords: Specific product terms, features, brands, skin types, concerns\n"
            "2. Intent: What the customer wants to do (buy, inquire, compare, recommend, review)\n"
            "3. Urgency: How urgent their need seems (high, medium, low)\n"
            "4. Price Range: Any mentioned budget or price preferences (e.g., \"under $50\", \"$20-100\")\n"
            "5. Preferences: Special requirements (organic, vegan, cruelty-free, hypoallergenic, etc.)\n\n"
            "Customer message: {message}\n\n"
            "Previous conversation context: {context}\n\n"
            "Consider beauty industry context:\n"
            "- Product categories: skincare, makeup, haircare, fragrance, tools\n"
            "- Skin concerns: acne, aging, dryness, sensitivity, pigmentation\n"
            "- Product types: foundation, lipstick, serum, moisturizer, cleanser, mascara\n"
            "- Brand preferences and ingredient preferences\n\n"
            "{format_instructions}"
        )

        self.keyword_parser = PydanticOutputParser(pydantic_object=KeywordExtraction)

        # Enhanced product matching with semantic similarity
        self.product_matching_prompt = ChatPromptTemplate.from_template(
            "You are a sophisticated product matching expert for beauty/cosmetics. Based on the extracted keywords, user intent, and preferences, find the most relevant products.\n\n"
            "Extracted data:\n"
            "- Keywords: {keywords}\n"
            "- User intent: {intent}\n"
            "- Urgency: {urgency}\n"
            "- Price range: {price_range}\n"
            "- Preferences: {preferences}\n\n"
            "Available products: {products}\n\n"
            "Use advanced matching criteria:\n"
            "1. Semantic similarity between keywords and product descriptions\n"
            "2. Tag overlap and category matching\n"
            "3. Price range compatibility\n"
            "4. User preference alignment (organic, vegan, etc.)\n"
            "5. Intent-based prioritization\n\n"
            "Return top matches with detailed confidence scores and reasoning."
        )

        # Initialize synonym dictionary for fuzzy matching
        self.synonym_dict = self._build_synonym_dictionary()

        # Initialize category mappings
        self.category_mappings = self._build_category_mappings()

    def _build_synonym_dictionary(self) -> Dict[str, List[str]]:
        """Build dictionary of product synonyms for fuzzy matching"""
        return {
            "moisturizer": ["moisturiser", "cream", "lotion", "hydrator", "hydrating cream"],
            "foundation": ["base", "concealer", "coverage", "tinted moisturizer"],
            "lipstick": ["lip color", "lipstick", "lip gloss", "lip stain", "lipliner"],
            "mascara": ["mascara", "lash", "eyelash", "volumizing mascara"],
            "skincare": ["skin care", "facial", "face care", "dermapen"],
            "serum": ["serum", "treatment", "essence", "ampoule"],
            "cleanser": ["cleanser", "face wash", "facial cleanser", "makeup remover"],
            "sunscreen": ["sunblock", "sunscreen", "spf", "sun protection"],
            "toner": ["toner", "astringent", "face mist", "hydrosol"],
            "eyeshadow": ["eye shadow", "eyeshadow", "shadow", "eye color"],
            "blush": ["blush", "cheek color", "rouge", "contour"],
            "highlighter": ["highlighter", "illuminator", "glow", "shimmer"],
            "concealer": ["concealer", "corrector", "color corrector", "spot concealer"],
            "eyebrow": ["brow", "eyebrow", "brow pencil", "brow gel"],
            "eyeliner": ["eyeliner", "liquid liner", "pencil liner", "gel liner"],
            "lip balm": ["lip balm", "chapstick", "lip treatment", "lip moisturizer"],
            "hair mask": ["hair mask", "hair treatment", "deep conditioner", "hair repair"],
            "shampoo": ["shampoo", "hair cleanser", "hair wash", "clarifying shampoo"],
            "conditioner": ["conditioner", "hair conditioner", "leave-in", "hair detangler"]
        }

    def _build_category_mappings(self) -> Dict[str, List[str]]:
        """Build mappings from keywords to product categories"""
        return {
            "skincare": ["moisturizer", "serum", "cleanser", "toner", "sunscreen", "mask", "treatment"],
            "makeup": ["foundation", "lipstick", "mascara", "eyeshadow", "blush", "highlighter", "concealer"],
            "haircare": ["shampoo", "conditioner", "hair mask", "hair treatment", "hair oil"],
            "fragrance": ["perfume", "cologne", "body mist", "scent", "eau de toilette"],
            "tools": ["brush", "sponge", "applicator", "mirror", "tweezer", "curler"]
        }

    async def extract_keywords(self, message: str, context: List[BaseMessage] = None) -> KeywordExtraction:
        """
        Extract keywords and intent from user message with enhanced analysis.

        Args:
            message: User's message
            context: Previous conversation messages

        Returns:
            KeywordExtraction: Extracted keywords, intent, urgency, price range, and preferences
        """
        try:
            # Format context for prompt
            context_str = ""
            if context:
                context_str = "\n".join([f"{msg.type}: {msg.content}" for msg in context[-5:]])

            # Create the chain
            if self.llm:
                chain = self.keyword_extraction_prompt | self.llm | self.keyword_parser
            else:
                # Fallback without LLM
                chain = self.keyword_extraction_prompt | self.keyword_parser

            # Run extraction
            if self.llm:
                result = await chain.ainvoke({
                    "message": message,
                    "context": context_str,
                    "format_instructions": self.keyword_parser.get_format_instructions()
                })
            else:
                # Fallback mode - return basic extraction
                result = self._fallback_keyword_extraction(message)

            self.logger.info(f"🔍 Enhanced extraction: {result.keywords}, Intent: {result.intent}, Preferences: {result.preferences}")
            return result

        except Exception as e:
            self.logger.error(f"Error extracting keywords: {e}")
            # Fallback extraction
            return self._fallback_keyword_extraction(message)

    def _fallback_keyword_extraction(self, message: str) -> KeywordExtraction:
        """
        Enhanced fallback keyword extraction using regex patterns and synonym matching.

        Args:
            message: User's message

        Returns:
            KeywordExtraction: Basic extracted keywords with enhanced analysis
        """
        # Simple regex-based extraction
        words = re.findall(r'\b\w+\b', message.lower())

        # Enhanced product-related keywords
        product_keywords = []
        for word in words:
            # Check direct matches
            if word in self.synonym_dict or any(word in synonyms for synonyms in self.synonym_dict.values()):
                product_keywords.append(word)
            # Check for longer meaningful words
            elif len(word) > 3 and not word in ['that', 'this', 'with', 'from', 'have', 'they', 'will', 'would']:
                product_keywords.append(word)

        # Extract price information
        price_range = self._extract_price_range(message)

        # Extract preferences
        preferences = self._extract_preferences(message)

        # Determine intent with better logic
        intent = "inquire"
        if any(word in message.lower() for word in ['buy', 'purchase', 'get', 'want', 'order', 'looking for']):
            intent = "buy"
        elif any(word in message.lower() for word in ['compare', 'vs', 'versus', 'difference', 'better']):
            intent = "compare"
        elif any(word in message.lower() for word in ['recommend', 'suggest', 'advice', 'help me choose']):
            intent = "recommend"

        # Determine urgency
        urgency = "medium"
        if any(word in message.lower() for word in ['urgent', 'asap', 'now', 'immediately', 'today', 'quick']):
            urgency = "high"
        elif any(word in message.lower() for word in ['later', 'maybe', 'thinking', 'eventually']):
            urgency = "low"

        return KeywordExtraction(
            keywords=list(set(product_keywords)),
            intent=intent,
            urgency=urgency,
            price_range=price_range,
            preferences=preferences
        )

    def _extract_price_range(self, message: str) -> Optional[Tuple[float, float]]:
        """Extract price range from message"""
        # Look for patterns like "$20-50", "under $30", "between 10 and 20 dollars"
        price_patterns = [
            r'\$(\d+)-?\$?(\d+)',  # $20-50 or $20 $50
            r'under \$(\d+)',      # under $30
            r'below \$(\d+)',      # below $30
            r'between (\d+) and (\d+) dollars?',  # between 10 and 20 dollars
            r'(\d+)-(\d+) dollars?'  # 10-20 dollars
        ]

        for pattern in price_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                if len(match.groups()) == 2:
                    min_price = float(match.group(1))
                    max_price = float(match.group(2))
                    return (min_price, max_price)
                elif len(match.groups()) == 1:
                    max_price = float(match.group(1))
                    return (0, max_price)

        return None

    def _extract_preferences(self, message: str) -> List[str]:
        """Extract user preferences from message"""
        preferences = []
        pref_keywords = {
            'organic': ['organic', 'natural', 'plant-based'],
            'vegan': ['vegan', 'cruelty-free', 'not tested on animals'],
            'hypoallergenic': ['hypoallergenic', 'sensitive skin', 'gentle'],
            'oil-free': ['oil-free', 'non-comedogenic', 'won\'t clog pores'],
            'spf': ['spf', 'sunscreen', 'sun protection'],
            'waterproof': ['waterproof', 'long-lasting', 'smudge-proof']
        }

        message_lower = message.lower()
        for pref, keywords in pref_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                preferences.append(pref)

        return preferences

    async def match_products(self, keywords: List[str], intent: str, urgency: str,
                           price_range: Optional[Tuple[float, float]] = None,
                           preferences: List[str] = None) -> List[ProductMatch]:
        """
        Enhanced product matching with multi-criteria scoring.

        Args:
            keywords: Extracted keywords
            intent: User intent
            urgency: Urgency level
            price_range: Optional price range filter
            preferences: User preferences

        Returns:
            List[ProductMatch]: Enhanced product matches with detailed scoring
        """
        try:
            # Get all products from database
            products = await self._get_all_products()

            if not products:
                self.logger.warning("No products found in database")
                return []

            # Enhanced matching with multiple criteria
            enhanced_matches = []

            for product in products:
                match = await self._calculate_enhanced_relevance(
                    product, keywords, intent, urgency, price_range, preferences or []
                )
                if match.confidence_score > 0.1:  # Only include relevant matches
                    enhanced_matches.append(match)

            # Sort by confidence score and return top matches
            enhanced_matches.sort(key=lambda x: x.confidence_score, reverse=True)

            top_matches = enhanced_matches[:7]  # Return top 7 matches for better selection

            self.logger.info(f"🎯 Enhanced matching found {len(top_matches)} product matches")
            return top_matches

        except Exception as e:
            self.logger.error(f"Error in enhanced product matching: {e}")
            return []

    async def _calculate_enhanced_relevance(self, product: Dict[str, Any],
                                          keywords: List[str], intent: str, urgency: str,
                                          price_range: Optional[Tuple[float, float]],
                                          preferences: List[str]) -> ProductMatch:
        """
        Calculate enhanced relevance score using multiple criteria.

        Args:
            product: Product dictionary
            keywords: Extracted keywords
            intent: User intent
            urgency: Urgency level
            price_range: Optional price range
            preferences: User preferences

        Returns:
            ProductMatch: Enhanced product match with detailed scoring
        """
        score = 0.0
        reasoning_parts = []

        product_name = product.get('name', '').lower()
        product_desc = product.get('description', '').lower()
        product_tags = [tag.lower() for tag in product.get('tags', [])]
        product_category = product.get('category', '').lower()
        product_price = product.get('price', 0.0)

        # 1. Enhanced keyword matching with synonyms
        keyword_score = 0.0
        for keyword in keywords:
            keyword_lower = keyword.lower()

            # Direct matches
            if keyword_lower in product_name:
                keyword_score += 0.4
                reasoning_parts.append(f"Keyword '{keyword}' in product name")
            elif keyword_lower in product_desc:
                keyword_score += 0.2
                reasoning_parts.append(f"Keyword '{keyword}' in description")

            # Synonym matching
            for main_term, synonyms in self.synonym_dict.items():
                if keyword_lower == main_term or keyword_lower in synonyms:
                    if main_term in product_name or any(syn in product_name for syn in synonyms):
                        keyword_score += 0.35
                        reasoning_parts.append(f"Synonym match: '{keyword}' ~ '{main_term}' in name")
                    elif main_term in product_desc or any(syn in product_desc for syn in synonyms):
                        keyword_score += 0.15
                        reasoning_parts.append(f"Synonym match: '{keyword}' ~ '{main_term}' in description")

            # Tag matching with synonyms
            for tag in product_tags:
                if keyword_lower == tag or tag in self.synonym_dict.get(keyword_lower, []):
                    keyword_score += 0.3
                    reasoning_parts.append(f"Tag match: '{keyword}' matches product tag")

        # 2. Category-based matching
        category_score = 0.0
        for keyword in keywords:
            for category, category_keywords in self.category_mappings.items():
                if keyword.lower() in category_keywords:
                    if category in product_category:
                        category_score += 0.25
                        reasoning_parts.append(f"Category match: '{keyword}' in {category}")

        # 3. Price compatibility
        price_score = 1.0  # Default full score if no price range specified
        if price_range:
            min_price, max_price = price_range
            if product_price < min_price:
                price_score = 0.3  # Too cheap
                reasoning_parts.append(f"Price too low: ${product_price} < ${min_price}")
            elif product_price > max_price:
                price_score = 0.5  # A bit expensive but still relevant
                reasoning_parts.append(f"Price slightly high: ${product_price} > ${max_price}")
            else:
                price_score = 1.0
                reasoning_parts.append(f"Price in range: ${product_price}")

        # 4. Preference alignment
        preference_score = 0.0
        if preferences:
            for pref in preferences:
                # Check if preference is mentioned in product description or tags
                pref_keywords = {
                    'organic': ['organic', 'natural', 'plant-based'],
                    'vegan': ['vegan', 'cruelty-free', 'not tested'],
                    'hypoallergenic': ['hypoallergenic', 'gentle', 'sensitive'],
                    'oil-free': ['oil-free', 'non-comedogenic'],
                    'spf': ['spf', 'sunscreen'],
                    'waterproof': ['waterproof', 'long-lasting']
                }

                if pref in pref_keywords:
                    pref_terms = pref_keywords[pref]
                    if any(term in product_desc for term in pref_terms) or \
                       any(term in ' '.join(product_tags) for term in pref_terms):
                        preference_score += 0.2
                        reasoning_parts.append(f"Preference match: {pref}")

        # 5. Semantic similarity (simplified version)
        semantic_score = min(len(set(keywords) & set(product_tags)) / max(len(keywords), 1), 1.0)

        # 6. Tag overlap
        tag_overlap = len(set(keywords) & set(product_tags)) / max(len(product_tags), 1)

        # Calculate final score with weighted factors
        weights = {
            'keyword_match': 0.35,
            'semantic_similarity': 0.20,
            'tag_overlap': 0.15,
            'category_match': 0.10,
            'price_compatibility': 0.10,
            'preference_alignment': 0.10
        }

        final_score = (min(keyword_score, 1.0) * weights['keyword_match'] +
                      semantic_score * weights['semantic_similarity'] +
                      tag_overlap * weights['tag_overlap'] +
                      min(category_score, 1.0) * weights['category_match'] +
                      price_score * weights['price_compatibility'] +
                      min(preference_score, 1.0) * weights['preference_alignment'])

        # Intent-based adjustments
        if intent == "buy":
            final_score *= 1.2
            reasoning_parts.append("Buying intent increases relevance")
        elif intent == "compare":
            final_score *= 0.9
            reasoning_parts.append("Comparison intent slightly reduces priority")

        # Urgency adjustment
        if urgency == "high":
            final_score *= 1.1
            reasoning_parts.append("High urgency increases relevance")

        # Normalize final score
        final_score = min(final_score, 1.0)

        reasoning = "; ".join(reasoning_parts) if reasoning_parts else "General product match"

        return ProductMatch(
            product=product,
            confidence_score=round(final_score, 3),
            reasoning=reasoning
        )

    async def _get_all_products(self) -> List[Dict[str, Any]]:
        """
        Get all products from the database with enhanced error handling.

        Returns:
            List[Dict]: List of product dictionaries
        """
        try:
            # Ensure postgres_handler is connected
            if not hasattr(postgres_handler, 'conn') or postgres_handler.conn is None or postgres_handler.conn.closed:
                postgres_handler.connect()

            # Use postgres_handler to get products with more fields
            query = """
            SELECT id, name, description, price, category_id, product_tag, is_active, stock_count, rating
            FROM products
            WHERE is_active = true AND stock_count > 0
            ORDER BY rating DESC, stock_count DESC
            """
            products = postgres_handler.execute_query(query)

            self.logger.info(f"Database query returned {len(products) if products else 0} products")

            # Convert to list of dicts with enhanced fields
            product_list = []
            for row in products:
                product_list.append({
                    'id': str(row['id']),
                    'name': row['name'],
                    'description': row['description'] or "",
                    'price': float(row['price']) if row['price'] else 0.0,
                    'category': row['category_id'] or "",
                    'tags': row['product_tag'] if isinstance(row['product_tag'], list) else [],
                    'rating': float(row['rating']) if row['rating'] else 0.0,
                    'stock_count': int(row['stock_count']) if row['stock_count'] else 0
                })

            self.logger.info(f"Successfully processed {len(product_list)} products")
            return product_list

        except Exception as e:
            self.logger.error(f"Error fetching products: {e}")
            import traceback
            traceback.print_exc()
            return []
