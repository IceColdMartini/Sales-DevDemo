#!/usr/bin/env python3
"""
Lightweight Enhanced Validation Test
===================================

Test enhanced stage detection without dependencies on external services.
"""

import asyncio
import time
import sys
import os

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.new_conversation.enhanced_sales_analyzer import EnhancedSalesFunnelAnalyzer

async def run_lightweight_validation():
    """Test our enhanced stage detection improvements."""
    
    print("🎯 LIGHTWEIGHT ENHANCED VALIDATION TEST")
    print("=" * 50)
    
    analyzer = EnhancedSalesFunnelAnalyzer()
    
    # Test scenarios that were failing in the focused test
    test_scenarios = [
        {
            "name": "Stage Detection Accuracy",
            "tests": [
                {"msg": "Hi, I'm looking for skincare products", "prev": "", "expected": "INITIAL_INTEREST"},
                {"msg": "Tell me about anti-aging serums", "prev": "INITIAL_INTEREST", "expected": "PRODUCT_DISCOVERY"},
                {"msg": "What's the price range?", "prev": "PRODUCT_DISCOVERY", "expected": "PRICE_EVALUATION"},
                {"msg": "I'd like to get the serum", "prev": "PRICE_EVALUATION", "expected": "PURCHASE_INTENT"},
                {"msg": "Yes, I'll take it", "prev": "PURCHASE_INTENT", "expected": "PURCHASE_CONFIRMATION"}
            ]
        },
        {
            "name": "Quick Purchase Flow",
            "tests": [
                {"msg": "I need a moisturizer under $30", "prev": "", "expected": "INITIAL_INTEREST"},
                {"msg": "That looks perfect, I'll take it", "prev": "INITIAL_INTEREST", "expected": "PURCHASE_CONFIRMATION"},
                {"msg": "How do I buy this?", "prev": "PURCHASE_CONFIRMATION", "expected": "PURCHASE_CONFIRMATION"}
            ]
        },
        {
            "name": "Product Information Extraction",
            "tests": [
                {"msg": "I want sulfate-free cleansers with salicylic acid", "prev": "", "expected": "INITIAL_INTEREST"},
                {"msg": "Do you have CeraVe or Neutrogena brands?", "prev": "INITIAL_INTEREST", "expected": "PRODUCT_DISCOVERY"}
            ]
        },
        {
            "name": "Edge Cases & Corrections",
            "tests": [
                {"msg": "I think I'd like to get that product", "prev": "PRICE_EVALUATION", "expected": "PURCHASE_INTENT"},
                {"msg": "What are the ingredients?", "prev": "INITIAL_INTEREST", "expected": "PRODUCT_DISCOVERY"},
                {"msg": "That sounds expensive", "prev": "PRODUCT_DISCOVERY", "expected": "PRICE_EVALUATION"},
                {"msg": "Actually, I'll go with the first option", "prev": "PRICE_EVALUATION", "expected": "PURCHASE_INTENT"}
            ]
        }
    ]
    
    overall_results = []
    
    for scenario in test_scenarios:
        print(f"\n📋 Testing: {scenario['name']}")
        scenario_results = []
        
        for test in scenario['tests']:
            # Test rule-based analysis directly
            result = analyzer._rule_based_analysis(test['msg'], test['prev'])
            
            if result:
                predicted = result.current_stage
                expected = test['expected']
                is_correct = predicted == expected
                
                scenario_results.append({
                    'message': test['msg'],
                    'expected': expected,
                    'predicted': predicted,
                    'correct': is_correct,
                    'confidence': result.confidence_score
                })
                
                status = "✅" if is_correct else "❌"
                msg_preview = test['msg'][:40] + "..." if len(test['msg']) > 40 else test['msg']
                print(f"  {status} '{msg_preview}' → {predicted} (conf: {result.confidence_score:.2f})")
                
                if not is_correct:
                    print(f"      Expected: {expected}, Got: {predicted}")
            else:
                scenario_results.append({
                    'message': test['msg'],
                    'expected': test['expected'],
                    'predicted': None,
                    'correct': False,
                    'confidence': 0.0
                })
                
                msg_preview = test['msg'][:40] + "..." if len(test['msg']) > 40 else test['msg']
                print(f"  ❌ '{msg_preview}' → No result")
        
        # Calculate scenario success rate
        correct_count = sum(1 for r in scenario_results if r['correct'])
        success_rate = correct_count / len(scenario_results) if scenario_results else 0
        
        overall_results.append({
            'name': scenario['name'],
            'results': scenario_results,
            'success_rate': success_rate,
            'correct_count': correct_count,
            'total_count': len(scenario_results)
        })
        
        print(f"  📊 Success Rate: {success_rate:.1%} ({correct_count}/{len(scenario_results)})")
    
    # Overall summary
    print(f"\n" + "="*50)
    print("📊 OVERALL VALIDATION RESULTS")
    print("="*50)
    
    total_tests = sum(r['total_count'] for r in overall_results)
    total_correct = sum(r['correct_count'] for r in overall_results)
    overall_success = total_correct / total_tests if total_tests > 0 else 0
    
    print(f"🎯 Overall Success Rate: {overall_success:.1%}")
    print(f"📈 Total Tests: {total_correct}/{total_tests}")
    
    print(f"\n📋 Scenario Breakdown:")
    for result in overall_results:
        status = "✅" if result['success_rate'] >= 0.8 else "⚠️" if result['success_rate'] >= 0.6 else "❌"
        print(f"  {status} {result['name']}: {result['success_rate']:.1%}")
    
    # Analysis and recommendations
    print(f"\n💡 Analysis:")
    
    if overall_success >= 0.9:
        print("  🎉 EXCELLENT: Enhanced stage detection is performing exceptionally well!")
    elif overall_success >= 0.8:
        print("  ✅ GOOD: Enhanced stage detection shows strong improvement")
    elif overall_success >= 0.7:
        print("  ⚠️  MODERATE: Enhanced stage detection is improving but needs refinement")
    else:
        print("  ❌ NEEDS WORK: Enhanced stage detection requires more improvements")
    
    # Confidence analysis
    all_confidences = []
    for result in overall_results:
        for test in result['results']:
            if test['confidence'] > 0:
                all_confidences.append(test['confidence'])
    
    if all_confidences:
        avg_confidence = sum(all_confidences) / len(all_confidences)
        print(f"  📊 Average Confidence: {avg_confidence:.2f}")
        
        if avg_confidence >= 0.8:
            print("  🎯 High confidence in predictions")
        elif avg_confidence >= 0.6:
            print("  ⚖️ Moderate confidence in predictions")
        else:
            print("  ⚠️ Low confidence suggests need for pattern refinement")
    
    return overall_success

if __name__ == "__main__":
    success_rate = asyncio.run(run_lightweight_validation())
    exit_code = 0 if success_rate >= 0.8 else 1
    sys.exit(exit_code)
