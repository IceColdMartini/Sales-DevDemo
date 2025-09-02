
from fastapi import APIRouter, Depends, HTTPException, status
from app.models.schemas import Message, ApiResponse
from app.services.enhanced_conversation_service import enhanced_conversation_service
from app.services.conversation_service import conversation_service  # Fallback service
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# Configuration flag for LangChain integration
USE_ENHANCED_SERVICE = True  # Set to False to use original service

@router.post("/webhook", response_model=ApiResponse)
async def handle_message(message: Message):
    """
    Enhanced webhook endpoint with LangChain-powered conversation processing.
    
    This endpoint provides production-ready conversation handling with:
    - LangChain-powered conversation chains for superior context understanding
    - Advanced sales funnel analysis with sophisticated purchase intent detection
    - Intelligent product matching and recommendation system
    - Error-resilient processing with automatic fallbacks
    - Enhanced conversation memory and state management
    
    Expected input format:
    {
        "sender": "facebook_profile_id",
        "recipient": "page_id", 
        "text": "user_message_text"
    }
    
    Returns enhanced response:
    {
        "sender": "facebook_profile_id",
        "product_interested": "product_name_or_null",
        "interested_product_ids": ["id1", "id2"],
        "response_text": "ai_generated_response", 
        "is_ready": false_or_true,
        "conversation_stage": "sales_funnel_stage",
        "langchain_powered": true,
        "keywords_extracted": ["keyword1", "keyword2"],
        "products_count": 2,
        "analysis_confidence": 0.95
    }
    """
    try:
        logger.info(f"🚀 Enhanced processing message from sender: {message.sender}")
        
        # Validate input
        if not message.sender or not message.text:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Sender ID and message text are required"
            )
        
        # Choose service based on configuration
        if USE_ENHANCED_SERVICE:
            try:
                # Process with enhanced LangChain service
                response = await enhanced_conversation_service.process_message(message)
                logger.info(f"✅ Enhanced processing completed for {message.sender}, Stage: {response.get('conversation_stage')}, Ready: {response['is_ready']}")
                return response
                
            except Exception as e:
                logger.warning(f"⚠️ Enhanced service failed, falling back to original: {e}")
                # Automatic fallback to original service
                response = await conversation_service.process_message(message)
                response['langchain_powered'] = False
                response['fallback_used'] = True
                return response
        else:
            # Use original service
            response = await conversation_service.process_message(message)
            response['langchain_powered'] = False
            logger.info(f"✅ Original processing completed for {message.sender}, Ready: {response['is_ready']}")
            return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing message from {message.sender}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while processing message"
        )

@router.get("/webhook/status/{sender_id}")
async def get_conversation_status(sender_id: str):
    """
    Get conversation statistics for a specific sender
    """
    try:
        from app.db.mongo_handler import mongo_handler
        stats = mongo_handler.get_conversation_stats(sender_id)
        
        return {
            "sender_id": sender_id,
            "stats": stats
        }
        
    except Exception as e:
        logger.error(f"Error getting conversation status for {sender_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving conversation status"
        )

@router.delete("/webhook/conversation/{sender_id}")
async def delete_conversation(sender_id: str):
    """
    Delete conversation history for a specific sender (for testing/reset purposes)
    """
    try:
        from app.db.mongo_handler import mongo_handler
        success = mongo_handler.delete_conversation(sender_id)
        
        if success:
            return {"message": f"Conversation deleted for sender: {sender_id}"}
        else:
            return {"message": f"No conversation found for sender: {sender_id}"}
            
    except Exception as e:
        logger.error(f"Error deleting conversation for {sender_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting conversation"
        )
