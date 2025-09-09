
from fastapi import APIRouter, Depends, HTTPException, status
from app.models.schemas import Message, ApiResponse
from app.services.conversation_backbone import conversation_backbone
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/webhook")
async def handle_message(message: Message):
    """
    Main webhook endpoint using the new conversation backbone.

    This endpoint provides state-of-the-art conversation handling with:
    - Advanced LangChain orchestrator for superior context understanding
    - Sophisticated product matching using product tags
    - Intelligent sales funnel analysis with purchase intent detection
    - Persistent conversation state management with MongoDB
    - Error-resilient processing with comprehensive logging

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
        "confidence": 0.95,
        "new_system": true
    }
    """
    try:
        logger.info(f"🚀 Processing message from sender: {message.sender}")

        # Validate input
        if not message.sender or not message.text:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Sender ID and message text are required"
            )

        # Process with the new conversation backbone
        response = await conversation_backbone.process_message(
            message.sender, message.text
        )

        # Convert to ApiResponse format
        api_response = ApiResponse(
            sender=response["sender"],
            product_interested=response["product_interested"],
            interested_product_ids=response["interested_product_ids"],
            response_text=response["response_text"],
            is_ready=response["is_ready"]
        )

        # Return as dict to include additional metadata for enhanced features
        # This maintains backward compatibility while providing extra data for testing
        response_dict = api_response.dict()
        response_dict.update({
            "conversation_stage": response.get("conversation_stage"),
            "confidence": response.get("confidence", 0.5),
            "handover": response.get("handover", False),
            "new_system": response.get("new_system", True),
            "metadata": response.get("metadata", {}),
            "processing_timestamp": response.get("processing_timestamp")
        })

        logger.info(f"✅ Message processed successfully for {message.sender}")
        return response_dict

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error processing message from {message.sender}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while processing message"
        )

@router.get("/webhook/status/{sender_id}")
async def get_conversation_status(sender_id: str):
    """
    Get conversation statistics for a specific sender using the new conversation backbone
    """
    try:
        # Use new conversation backbone
        status = await conversation_backbone.get_conversation_status(sender_id)
        return {
            "sender_id": sender_id,
            "status": status,
            "system": "conversation_backbone"
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
    Delete conversation history for a specific sender using the new conversation backbone
    """
    try:
        # Use new conversation backbone
        success = await conversation_backbone.clear_conversation(sender_id)
        if success:
            return {"message": f"Conversation for {sender_id} deleted successfully"}
        else:
            return {"message": f"Failed to delete conversation for {sender_id}"}

    except Exception as e:
        logger.error(f"Error deleting conversation for {sender_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting conversation"
        )

@router.get("/webhook/recommendations/{sender_id}")
async def get_product_recommendations(sender_id: str, query: str = None):
    """
    Get personalized product recommendations for a specific sender using the new conversation backbone
    """
    try:
        # Use new conversation backbone for recommendations
        recommendations = await conversation_backbone.get_product_recommendations(sender_id, query)

        return {
            "sender_id": sender_id,
            "recommendations": recommendations,
            "count": len(recommendations),
            "query": query,
            "system": "conversation_backbone"
        }

    except Exception as e:
        logger.error(f"Error getting recommendations for {sender_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving product recommendations"
        )

@router.get("/webhook/insights/{sender_id}")
async def get_conversation_insights(sender_id: str):
    """
    Get advanced conversation insights for a specific sender using the new conversation backbone
    """
    try:
        # Use new conversation backbone for insights
        insights = await conversation_backbone.get_conversation_insights(sender_id)

        return {
            "sender_id": sender_id,
            "insights": insights,
            "system": "conversation_backbone"
        }

    except Exception as e:
        logger.error(f"Error getting insights for {sender_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving conversation insights"
        )
