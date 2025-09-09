"""
Enhanced New Conversation System Exports
========================================

Exports enhanced conversation modules for improved performance.
"""

from .orchestrator import conversation_orchestrator
from .enhanced_sales_analyzer import enhanced_sales_analyzer
from .enhanced_product_matcher import enhanced_product_matcher
from .enhanced_response_generator import enhanced_response_generator, ResponseContext
from .state_manager import conversation_state_manager

# Legacy imports for backwards compatibility
try:
    from .sales_analyzer import sales_analyzer
    from .product_matcher import product_matcher
    from .response_generator import response_generator
except ImportError:
    # Enhanced modules are the new defaults
    sales_analyzer = enhanced_sales_analyzer
    product_matcher = enhanced_product_matcher
    response_generator = enhanced_response_generator

# Export the shared data structures
from . import ConversationState, ProductMatch, ConversationResponse

__all__ = [
    'conversation_orchestrator',
    'enhanced_sales_analyzer',
    'enhanced_product_matcher', 
    'enhanced_response_generator',
    'ResponseContext',
    'conversation_state_manager',
    'ConversationState',
    'ProductMatch', 
    'ConversationResponse',
    # Legacy exports for compatibility
    'sales_analyzer', 
    'product_matcher',
    'response_generator'
]
