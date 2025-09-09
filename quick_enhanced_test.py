"""
Quick Test for Enhanced Modules
===============================

Simple test to verify the enhanced modules work correctly.
"""

import asyncio
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)

async def test_enhanced_modules():
    """Test the enhanced modules individually."""
    
    print("🔧 Testing Enhanced Sales Analyzer...")
    try:
        from app.services.new_conversation.enhanced_sales_analyzer import enhanced_sales_analyzer
        from langchain_core.messages import HumanMessage
        
        # Test basic analysis
        conversation = [HumanMessage(content="Hi, I need skincare products")]
        analysis = await enhanced_sales_analyzer.analyze_conversation(
            conversation, [], "INITIAL_INTEREST", "I want to buy this serum"
        )
        print(f"✅ Sales Analyzer: Stage={analysis.current_stage}, Ready={analysis.is_ready_to_buy}")
        
    except Exception as e:
        print(f"❌ Sales Analyzer failed: {e}")
    
    print("\n🔧 Testing Enhanced Product Matcher...")
    try:
        from app.services.new_conversation.enhanced_product_matcher import enhanced_product_matcher
        
        # Mock products for testing
        mock_products = [
            {"id": "1", "name": "CeraVe Hydrating Cleanser", "category": "cleanser", "price": 12.99, "brand": "CeraVe"},
            {"id": "2", "name": "Neutrogena Retinol Serum", "category": "serum", "price": 24.99, "brand": "Neutrogena"}
        ]
        
        matches = await enhanced_product_matcher.find_matching_products(
            "I need a gentle cleanser", [], mock_products
        )
        print(f"✅ Product Matcher: Found {len(matches)} matches")
        
    except Exception as e:
        print(f"❌ Product Matcher failed: {e}")
    
    print("\n🔧 Testing Enhanced Response Generator...")
    try:
        from app.services.new_conversation.enhanced_response_generator import enhanced_response_generator, ResponseContext
        
        context = ResponseContext(
            customer_message="I need skincare help",
            sales_stage="INITIAL_INTEREST",
            is_ready_to_buy=False,
            conversation_history=[],
            matched_products=[],
            customer_sentiment="neutral",
            conversation_length=1,
            previous_topics=[]
        )
        
        response = await enhanced_response_generator.generate_response(context)
        print(f"✅ Response Generator: Generated {len(response['message'])} character response")
        
    except Exception as e:
        print(f"❌ Response Generator failed: {e}")
    
    print("\n🔧 Testing Orchestrator Integration...")
    try:
        from app.services.new_conversation.orchestrator import conversation_orchestrator
        
        # This will test the full integration
        response = await conversation_orchestrator.process_message("test_user", "Hi, I need skincare help")
        print(f"✅ Orchestrator: Stage={response.sales_stage}, Response={response.response_text[:50]}...")
        
    except Exception as e:
        print(f"❌ Orchestrator failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_enhanced_modules())
