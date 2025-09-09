"""
Advanced LangChain Conversation System
=====================================

A complete rebuild of the conversation system using LangChain and LangGraph
for seamless, human-like customer interactions.
"""

from typing import Dict, List, Any, Optional, Tuple
import logging
import asyncio
from datetime import datetime
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# LangChain imports with version compatibility
try:
    from langchain_openai import AzureChatOpenAI
except ImportError:
    try:
        from langchain_community.chat_models import AzureChatOpenAI
    except ImportError:
        try:
            from langchain.chat_models import AzureChatOpenAI
        except ImportError:
            # Fallback for older versions
            AzureChatOpenAI = None
            logger.warning("AzureChatOpenAI not available - using fallback mode")

from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langchain_community.chat_message_histories import ChatMessageHistory

# Database imports
from app.db.postgres_handler import postgres_handler
from app.db.mongo_handler import mongo_handler
from app.core.config import settings

logger = logging.getLogger(__name__)

@dataclass
class ConversationState:
    """Represents the current state of a conversation"""
    sender_id: str
    current_stage: str = "INITIAL_INTEREST"
    interested_products: List[Dict] = field(default_factory=list)
    product_ids: List[str] = field(default_factory=list)
    is_ready_to_buy: bool = False
    conversation_history: List[BaseMessage] = field(default_factory=list)
    last_interaction: datetime = field(default_factory=datetime.now)
    context: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ProductMatch:
    """Represents a matched product with confidence score"""
    product: Dict
    confidence_score: float
    reasoning: str

@dataclass
class ConversationResponse:
    """Standardized response format"""
    sender: str
    product_interested: Optional[str]
    interested_product_ids: List[str]
    response_text: str
    is_ready: bool
    sales_stage: str
    confidence: float
    handover: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
