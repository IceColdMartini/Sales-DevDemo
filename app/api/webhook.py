
from fastapi import APIRouter, Depends, HTTPException, status
from app.models.schemas import Message, ApiResponse
from app.services.conversation_service import conversation_service
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/webhook", response_model=ApiResponse)
async def handle_message(message: Message):
    """
    This endpoint receives a message from the Routing Agent,
    processes it, and returns a response with product recommendations
    and conversation status.
    
    Expected input format:
    {
        "sender": "facebook_profile_id",
        "recipient": "page_id", 
        "text": "user_message_text"
    }
    
    Returns:
    {
        "sender": "facebook_profile_id",
        "product_interested": "product_name_or_null",
        "response_text": "ai_generated_response", 
        "is_ready": false_or_true
    }
    """
    try:
        logger.info(f"Processing message from sender: {message.sender}")
        
        # Validate input
        if not message.sender or not message.text:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Sender ID and message text are required"
            )
        
        # Process the message
        response = await conversation_service.process_message(message)
        
        logger.info(f"Successfully processed message for sender: {message.sender}, is_ready: {response['is_ready']}")
        
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
