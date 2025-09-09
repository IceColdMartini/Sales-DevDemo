"""
Conversation State Manager
==========================

Manages conversation state and memory using MongoDB for persistence.
"""

import logging
from typing import Dict, List, Any, Optional
import asyncio
from datetime import datetime
from decimal import Decimal

logger = logging.getLogger(__name__)

from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langchain_community.chat_message_histories import ChatMessageHistory
try:
    from langchain.memory import ConversationBufferWindowMemory
except ImportError:
    try:
        from langchain_community.memory import ConversationBufferWindowMemory
    except ImportError:
        # Fallback for newer versions - use basic chat history
        ConversationBufferWindowMemory = ChatMessageHistory
        logger.warning("ConversationBufferWindowMemory not available - using ChatMessageHistory")

from app.db.mongo_handler import mongo_handler
from . import ConversationState

def _convert_decimals(obj):
    """Convert Decimal objects to float for MongoDB compatibility."""
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, dict):
        return {key: _convert_decimals(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [_convert_decimals(item) for item in obj]
    else:
        return obj

class ConversationStateManager:
    """
    Manages conversation state and memory persistence.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.memory_cache = {}  # Cache for LangChain memory objects

    async def get_conversation_state(self, sender_id: str) -> ConversationState:
        """
        Get or create conversation state for a sender.

        Args:
            sender_id: Unique identifier for the conversation

        Returns:
            ConversationState: Current state of the conversation
        """
        try:
            # Try to get existing conversation from MongoDB
            conversation_data = mongo_handler.get_conversation(sender_id)

            if conversation_data:
                # Handle different data structures gracefully
                conversation_state = self._parse_conversation_data(sender_id, conversation_data)
            else:
                # Create new conversation state
                conversation_state = ConversationState(sender_id=sender_id)

            # Initialize LangChain memory if not already cached
            if sender_id not in self.memory_cache:
                self.memory_cache[sender_id] = ConversationBufferWindowMemory(
                    k=20,  # Remember last 20 exchanges
                    return_messages=True,
                    memory_key="chat_history"
                )

                # Load existing messages into memory
                for msg in conversation_state.conversation_history[-20:]:
                    if hasattr(msg, 'type') and msg.type == 'human':
                        self.memory_cache[sender_id].chat_memory.add_message(msg)
                    elif hasattr(msg, 'type') and msg.type == 'ai':
                        self.memory_cache[sender_id].chat_memory.add_message(msg)

            return conversation_state

        except Exception as e:
            self.logger.error(f"Error getting conversation state for {sender_id}: {e}")
            # Return new state on error
            return ConversationState(sender_id=sender_id)

    def _parse_conversation_data(self, sender_id: str, conversation_data: Dict[str, Any]) -> ConversationState:
        """
        Parse MongoDB conversation data into ConversationState object.
        Handles various data structure formats gracefully.

        Args:
            sender_id: Unique identifier for the conversation
            conversation_data: Raw conversation data from MongoDB

        Returns:
            ConversationState: Parsed conversation state
        """
        try:
            # Initialize default values
            conversation_history = []
            interested_products = []
            product_ids = []
            current_stage = "INITIAL_INTEREST"
            is_ready = False

            # Extract messages from various possible structures
            messages = []
            if isinstance(conversation_data, dict):
                # Try different possible structures
                if 'conversation' in conversation_data:
                    conv_field = conversation_data['conversation']
                    if isinstance(conv_field, list):
                        messages = conv_field
                    elif isinstance(conv_field, dict) and 'conversation' in conv_field:
                        messages = conv_field['conversation']
                    elif isinstance(conv_field, dict) and 'messages' in conv_field:
                        messages = conv_field['messages']
                elif 'messages' in conversation_data:
                    messages = conversation_data['messages']
                elif isinstance(conversation_data.get('conversation'), list):
                    messages = conversation_data['conversation']

            # Ensure messages is a list
            if not isinstance(messages, list):
                messages = []

            # Parse messages into LangChain format
            for msg_data in messages:
                if isinstance(msg_data, dict):
                    role = msg_data.get('role', 'user')
                    content = msg_data.get('content', '')

                    if role == 'user':
                        conversation_history.append(HumanMessage(content=content))
                    elif role == 'assistant':
                        conversation_history.append(AIMessage(content=content))

                        # Extract state information from assistant messages
                        if isinstance(content, str):
                            content_lower = content.lower()
                            if any(keyword in content_lower for keyword in ['ready to buy', 'confirm purchase', 'proceed with purchase']):
                                is_ready = True
                                current_stage = "PURCHASE_CONFIRMATION"
                            elif any(keyword in content_lower for keyword in ['interested', 'considering', 'thinking about']):
                                current_stage = "PURCHASE_INTENT"
                            elif any(keyword in content_lower for keyword in ['price', 'cost', 'budget', 'afford']):
                                current_stage = "PRICE_EVALUATION"
                            elif any(keyword in content_lower for keyword in ['recommend', 'suggest', 'options']):
                                current_stage = "PRODUCT_DISCOVERY"

            # Extract product information if available
            if 'product_ids' in conversation_data:
                product_ids = conversation_data['product_ids'] if isinstance(conversation_data['product_ids'], list) else []
            if 'interested_products' in conversation_data:
                interested_products = conversation_data['interested_products'] if isinstance(conversation_data['interested_products'], list) else []

            return ConversationState(
                sender_id=sender_id,
                current_stage=current_stage,
                interested_products=interested_products,
                product_ids=product_ids,
                is_ready_to_buy=is_ready,
                conversation_history=conversation_history
            )

        except Exception as e:
            self.logger.error(f"Error parsing conversation data for {sender_id}: {e}")
            # Return basic state on parsing error
            return ConversationState(sender_id=sender_id)

    async def update_conversation_state(self, sender_id: str, sales_analysis: Any,
                                      matched_products: List[Any]) -> None:
        """
        Update the conversation state with new analysis and products.

        Args:
            sender_id: Unique identifier for the conversation
            sales_analysis: Sales analysis results
            matched_products: List of matched products
        """
        try:
            # Get current conversation data
            conversation_data = mongo_handler.get_conversation(sender_id)

            if not conversation_data:
                # Create new conversation structure if it doesn't exist
                conversation_data = {
                    'sender_id': sender_id,
                    'conversation': [],
                    'current_stage': 'INITIAL_INTEREST',
                    'is_ready': False,
                    'product_ids': [],
                    'interested_products': [],
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat()
                }

            # Update with sales analysis results
            if sales_analysis:
                conversation_data['current_stage'] = getattr(sales_analysis, 'current_stage', 'INITIAL_INTEREST')
                conversation_data['is_ready'] = getattr(sales_analysis, 'is_ready_to_buy', False)

            # Update products if new ones were matched (accumulate, don't reset)
            if matched_products:
                # Get existing product data
                existing_product_ids = set(conversation_data.get('product_ids', []))
                existing_products = conversation_data.get('interested_products', [])
                
                new_product_ids = []
                new_interested_products = []

                for product_match in matched_products:
                    if hasattr(product_match, 'product') and product_match.product:
                        product_data = product_match.product
                        
                        # Extract product ID if available
                        product_id = None
                        if isinstance(product_data, dict) and 'id' in product_data:
                            product_id = product_data['id']
                        elif hasattr(product_data, 'get') and callable(product_data.get):
                            product_id = product_data.get('id')
                        
                        # Only add if not already tracked
                        if product_id and product_id not in existing_product_ids:
                            new_product_ids.append(product_id)
                            new_interested_products.append(product_data)
                            existing_product_ids.add(product_id)

                # Accumulate products (keep existing + add new)
                all_product_ids = list(existing_product_ids) + new_product_ids
                all_products = existing_products + new_interested_products
                
                conversation_data['product_ids'] = all_product_ids
                conversation_data['interested_products'] = all_products
                
                self.logger.info(f"🎯 Product tracking updated: {len(existing_product_ids)} existing + {len(new_product_ids)} new = {len(all_product_ids)} total")

            # Update timestamp
            conversation_data['updated_at'] = datetime.now().isoformat()

            # Convert Decimals to floats before saving to MongoDB
            conversation_data = _convert_decimals(conversation_data)

            # Save updated conversation data
            mongo_handler.save_conversation(sender_id, conversation_data)

            self.logger.info(f"✅ Updated conversation state for {sender_id}: Stage={conversation_data.get('current_stage')}, Ready={conversation_data.get('is_ready')}")

        except Exception as e:
            self.logger.error(f"Error updating conversation state for {sender_id}: {e}")
            # Don't raise exception, just log it

    async def add_message_to_history(self, sender_id: str, role: str, content: str) -> None:
        """
        Add a message to the conversation history.

        Args:
            sender_id: Unique identifier for the conversation
            role: 'user' or 'assistant'
            content: Message content
        """
        try:
            # Get existing conversation
            conversation_data = mongo_handler.get_conversation(sender_id)

            if not conversation_data:
                # Create new conversation structure
                conversation_data = {
                    'sender_id': sender_id,
                    'conversation': [],
                    'current_stage': 'INITIAL_INTEREST',
                    'is_ready': False,
                    'product_ids': [],
                    'interested_products': [],
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat()
                }
            elif not isinstance(conversation_data, dict):
                # Handle case where conversation_data is not a dict
                self.logger.warning(f"Invalid conversation data type for {sender_id}: {type(conversation_data)}")
                conversation_data = {
                    'sender_id': sender_id,
                    'conversation': [],
                    'current_stage': 'INITIAL_INTEREST',
                    'is_ready': False,
                    'product_ids': [],
                    'interested_products': [],
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat()
                }

            # Ensure conversation field exists and is a list
            if 'conversation' not in conversation_data:
                conversation_data['conversation'] = []

            if not isinstance(conversation_data['conversation'], list):
                self.logger.warning(f"Conversation field is not a list for {sender_id}, resetting to empty list")
                conversation_data['conversation'] = []

            # Add new message
            new_message = {
                'role': role,
                'content': content,
                'timestamp': datetime.now().isoformat()
            }

            conversation_data['conversation'].append(new_message)
            conversation_data['updated_at'] = datetime.now().isoformat()

            # Keep only last 50 messages to prevent database bloat
            if len(conversation_data['conversation']) > 50:
                conversation_data['conversation'] = conversation_data['conversation'][-50:]

            # Save to MongoDB
            mongo_handler.save_conversation(sender_id, conversation_data)

            # Update LangChain memory cache
            if sender_id in self.memory_cache:
                if role == 'user':
                    self.memory_cache[sender_id].chat_memory.add_message(HumanMessage(content=content))
                elif role == 'assistant':
                    self.memory_cache[sender_id].chat_memory.add_message(AIMessage(content=content))

        except Exception as e:
            self.logger.error(f"Error adding message to history for {sender_id}: {e}")
            # Don't raise exception, just log it

    async def clear_conversation_state(self, sender_id: str) -> None:
        """
        Clear all conversation data for a sender.

        Args:
            sender_id: Unique identifier for the conversation
        """
        try:
            # Clear MongoDB conversation
            mongo_handler.delete_conversation(sender_id)

            # Clear memory cache
            if sender_id in self.memory_cache:
                del self.memory_cache[sender_id]

            self.logger.info(f"🗑️ Cleared conversation state for {sender_id}")

        except Exception as e:
            self.logger.error(f"Error clearing conversation state for {sender_id}: {e}")

    def get_langchain_memory(self, sender_id: str) -> Optional[Any]:
        """
        Get the LangChain memory object for a sender.

        Args:
            sender_id: Unique identifier for the conversation

        Returns:
            ConversationBufferWindowMemory or None if not found
        """
        return self.memory_cache.get(sender_id)

# Create global instance
conversation_state_manager = ConversationStateManager()
