from openai import AzureOpenAI
from app.core.config import settings
from typing import List, Tuple
import re
import os

class AIService:
    def __init__(self):
        # Use both environment variable names for compatibility
        endpoint = settings.AZURE_OPENAI_ENDPOINT or os.getenv("ENDPOINT_URL")
        api_key = settings.AZURE_OPENAI_API_KEY
        deployment = settings.OPENAI_MODEL or os.getenv("DEPLOYMENT_NAME", "gpt-4.1-nano")
        
        self.client = AzureOpenAI(
            azure_endpoint=endpoint,
            api_key=api_key,
            api_version=settings.OPENAI_API_VERSION,
        )
        self.deployment = deployment

    def get_keywords(self, text: str, product_context: str) -> List[str]:
        """Extract relevant keywords from user message based on product context"""
        messages = [
            {
                "role": "system",
                "content": "You are an expert in extracting relevant keywords from a user's message based on product context. Extract only the most important keywords that relate to the products being sold."
            },
            {
                "role": "user",
                "content": f"""
                Product Context: {product_context}
                User Message: {text}
                
                Extract the most important keywords from the user message that relate to the product context.
                Return only the keywords as a comma-separated list, no explanations.
                Focus on product categories, features, and user intent.
                """
            }
        ]
        
        try:
            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=messages,
                max_tokens=50,
                temperature=0.2,
            )
            keywords_text = response.choices[0].message.content.strip()
            keywords = [kw.strip() for kw in keywords_text.split(',') if kw.strip()]
            return keywords
        except Exception as e:
            print(f"Error extracting keywords: {e}")
            # Fallback: simple keyword extraction
            return [word.lower() for word in text.split() if len(word) > 3]

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
