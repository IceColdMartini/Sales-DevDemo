#!/usr/bin/env python3
"""
Quick Stage Detection Test
==========================

Test the enhanced stage detection improvements.
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.new_conversation.enhanced_sales_analyzer import EnhancedSalesFunnelAnalyzer

async def test_stage_detection():
    """Test improved stage detection logic."""
    
    analyzer = EnhancedSalesFunnelAnalyzer()
    
    # Test cases that were failing
    test_cases = [
        {
            "message": "Hi, I'm looking for skincare products",
            "previous_stage": "",
            "expected": "INITIAL_INTEREST"
        },
        {
            "message": "I need a moisturizer under $30",
            "previous_stage": "",
            "expected": "INITIAL_INTEREST"
        },
        {
            "message": "I want sulfate-free cleansers with salicylic acid",
            "previous_stage": "",
            "expected": "INITIAL_INTEREST"
        },
        {
            "message": "I'd like to get the serum",
            "previous_stage": "PRICE_EVALUATION",
            "expected": "PURCHASE_INTENT"
        },
        {
            "message": "That looks perfect, I'll take it",
            "previous_stage": "PRICE_EVALUATION", 
            "expected": "PURCHASE_CONFIRMATION"
        },
        {
            "message": "Do you have CeraVe or Neutrogena brands?",
            "previous_stage": "INITIAL_INTEREST",
            "expected": "PRODUCT_DISCOVERY"
        }
    ]
    
    print("🎯 Testing Enhanced Stage Detection")
    print("=" * 50)
    
    correct = 0
    total = len(test_cases)
    
    for i, test_case in enumerate(test_cases, 1):
        # Use rule-based analysis directly
        result = analyzer._rule_based_analysis(
            test_case["message"], 
            test_case["previous_stage"]
        )
        
        if result:
            predicted = result.current_stage
            expected = test_case["expected"]
            is_correct = predicted == expected
            
            if is_correct:
                correct += 1
            
            status = "✅" if is_correct else "❌"
            print(f"{status} Test {i}: '{test_case['message'][:40]}...'")
            print(f"    Expected: {expected}, Got: {predicted}")
            print(f"    Confidence: {result.confidence_score:.2f}")
            print()
        else:
            print(f"❌ Test {i}: No result returned")
            print()
    
    accuracy = (correct / total) * 100
    print(f"🎯 Stage Detection Accuracy: {accuracy:.1f}% ({correct}/{total})")
    
    return accuracy

if __name__ == "__main__":
    asyncio.run(test_stage_detection())
