"""
Enhanced Multi-Scenario Test Suite
=================================

Comprehensive testing with focus on fixing the 40% failure rate.
Targets specific issues identified in previous test results.
"""

import asyncio
import json
import time
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from fastapi.testclient import TestClient
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class EnhancedValidationCriteria:
    """Enhanced validation criteria with specific targets."""
    # Stage Detection Criteria (addressing main failure point)
    expected_stage_keywords: Dict[str, List[str]]
    stage_progression_required: bool
    purchase_intent_triggers: List[str]
    purchase_confirmation_triggers: List[str]
    stage_confidence_threshold: float = 0.7
    readiness_accuracy_threshold: float = 0.8
    
    # Response Quality Criteria
    min_response_length: int = 50
    max_response_length: int = 400
    required_tone: str = "friendly"
    must_include_keywords: List[str] = None
    must_avoid_keywords: List[str] = None
    
    # Product Matching Criteria
    min_product_matches: int = 0
    expected_product_categories: List[str] = None
    product_relevance_threshold: float = 0.5
    
    # Performance Criteria
    max_response_time: float = 8.0
    consistency_threshold: float = 0.8

@dataclass
class EnhancedTestScenario:
    """Enhanced test scenario with detailed validation."""
    name: str
    customer_type: str
    conversation_flow: List[Dict[str, str]]
    validation_criteria: List[EnhancedValidationCriteria]
    success_threshold: float = 0.75
    focus_areas: List[str] = None

class EnhancedMultiScenarioTester:
    """Enhanced multi-scenario tester targeting specific failure points."""

    def __init__(self):
        self.client = TestClient(self._get_app())
        self.test_results = []
        self.performance_metrics = []
        
        # Enhanced test scenarios targeting specific issues
        self.scenarios = self._create_enhanced_scenarios()

    def _get_app(self):
        """Get the FastAPI app for testing."""
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        from main import app
        return app

    def _create_enhanced_scenarios(self) -> List[EnhancedTestScenario]:
        """Create enhanced test scenarios targeting specific failure points."""
        
        return [
            # Scenario 1: Stage Detection Accuracy Test
            EnhancedTestScenario(
                name="Stage_Detection_Precision",
                customer_type="Stage_Progression_Tester",
                conversation_flow=[
                    {"role": "customer", "message": "Hi, I'm looking for skincare products"},
                    {"role": "customer", "message": "Tell me about anti-aging serums with retinol"},
                    {"role": "customer", "message": "What's the price of the retinol serum?"},
                    {"role": "customer", "message": "I'd like to get the retinol serum, it sounds perfect"},
                    {"role": "customer", "message": "Yes, I'll take it. How do I complete my purchase?"}
                ],
                validation_criteria=[
                    EnhancedValidationCriteria(
                        expected_stage_keywords={"INITIAL_INTEREST": ["looking", "need"], 
                                               "PRODUCT_DISCOVERY": ["tell me", "about"], 
                                               "PRICE_EVALUATION": ["price", "cost"],
                                               "PURCHASE_INTENT": ["I'd like", "sounds perfect"],
                                               "PURCHASE_CONFIRMATION": ["I'll take", "complete purchase"]},
                        stage_progression_required=True,
                        purchase_intent_triggers=["I'd like to get", "sounds perfect"],
                        purchase_confirmation_triggers=["I'll take it", "complete my purchase"],
                        min_response_length=60,
                        max_response_length=300,
                        required_tone="friendly",
                        max_response_time=7.0
                    )
                ],
                success_threshold=0.9,
                focus_areas=["stage_detection", "purchase_readiness"]
            ),

            # Scenario 2: Quick Buyer Fix (Previously failing at 33.3%)
            EnhancedTestScenario(
                name="Quick_Buyer_Enhanced",
                customer_type="Decisive_Quick_Buyer",
                conversation_flow=[
                    {"role": "customer", "message": "I need a good moisturizer for dry skin, something under $30"},
                    {"role": "customer", "message": "That looks perfect. I'll take the CeraVe moisturizer"},
                    {"role": "customer", "message": "Yes, I want to buy it now. How do I purchase?"}
                ],
                validation_criteria=[
                    EnhancedValidationCriteria(
                        expected_stage_keywords={"INITIAL_INTEREST": ["need"], 
                                               "PURCHASE_INTENT": ["looks perfect", "I'll take"],
                                               "PURCHASE_CONFIRMATION": ["want to buy", "how do I purchase"]},
                        stage_progression_required=True,
                        purchase_intent_triggers=["I'll take"],
                        purchase_confirmation_triggers=["want to buy", "how do I purchase"],
                        min_response_length=50,
                        max_response_length=250,
                        required_tone="friendly",
                        min_product_matches=1,
                        expected_product_categories=["moisturizer"],
                        max_response_time=6.0
                    )
                ],
                success_threshold=0.85,
                focus_areas=["quick_purchase_flow", "stage_detection", "product_matching"]
            ),

            # Scenario 3: Hesitant Customer Fix (Previously failing at 25%)
            EnhancedTestScenario(
                name="Hesitant_Customer_Enhanced",
                customer_type="Cautious_Decision_Maker",
                conversation_flow=[
                    {"role": "customer", "message": "I'm looking for acne products but I'm worried about irritation"},
                    {"role": "customer", "message": "What ingredients should I avoid? I have sensitive skin"},
                    {"role": "customer", "message": "Are there any gentle options that actually work?"},
                    {"role": "customer", "message": "The CeraVe cleanser sounds good, but I'm still not sure"},
                    {"role": "customer", "message": "Okay, I trust your recommendation. I'll try the cleanser"}
                ],
                validation_criteria=[
                    EnhancedValidationCriteria(
                        expected_stage_keywords={"INITIAL_INTEREST": ["looking for", "worried"], 
                                               "PRODUCT_DISCOVERY": ["ingredients", "gentle options"],
                                               "PRICE_EVALUATION": ["sounds good", "not sure"],
                                               "PURCHASE_INTENT": ["trust", "I'll try"]},
                        stage_progression_required=True,
                        purchase_intent_triggers=["I trust", "I'll try"],
                        purchase_confirmation_triggers=["I'll take", "let's do this"],
                        min_response_length=80,
                        max_response_length=350,
                        required_tone="friendly",
                        must_include_keywords=["gentle", "sensitive"],
                        min_product_matches=1,
                        expected_product_categories=["cleanser"],
                        max_response_time=7.5
                    )
                ],
                success_threshold=0.80,
                focus_areas=["concern_addressing", "trust_building", "gentle_progression"]
            ),

            # Scenario 4: Information Extraction Test
            EnhancedTestScenario(
                name="Information_Extraction_Test",
                customer_type="Detail_Oriented_Researcher",
                conversation_flow=[
                    {"role": "customer", "message": "I want sulfate-free cleansers for combination skin with salicylic acid"},
                    {"role": "customer", "message": "Tell me about the ingredients and pH levels"},
                    {"role": "customer", "message": "Do you have anything from Neutrogena or CeraVe brands?"},
                    {"role": "customer", "message": "The Neutrogena cleanser seems perfect for my needs"}
                ],
                validation_criteria=[
                    EnhancedValidationCriteria(
                        expected_stage_keywords={"INITIAL_INTEREST": ["want", "sulfate-free"], 
                                               "PRODUCT_DISCOVERY": ["ingredients", "pH levels"],
                                               "PRODUCT_DISCOVERY": ["Neutrogena", "CeraVe"],
                                               "PURCHASE_INTENT": ["seems perfect"]},
                        stage_progression_required=True,
                        purchase_intent_triggers=["seems perfect"],
                        purchase_confirmation_triggers=["I'll take", "purchase"],
                        min_response_length=70,
                        max_response_length=320,
                        required_tone="professional",
                        must_include_keywords=["ingredients", "cleanser"],
                        min_product_matches=1,
                        expected_product_categories=["cleanser"],
                        max_response_time=7.0
                    )
                ],
                success_threshold=0.85,
                focus_areas=["information_extraction", "brand_matching", "technical_details"]
            ),

            # Scenario 5: Purchase Completion Flow
            EnhancedTestScenario(
                name="Purchase_Completion_Flow",
                customer_type="Ready_to_Buy_Customer",
                conversation_flow=[
                    {"role": "customer", "message": "I've been using CeraVe products and love them"},
                    {"role": "customer", "message": "I want to order the CeraVe Hydrating Cleanser"},
                    {"role": "customer", "message": "Yes, I'm ready to buy it now. Let's complete the purchase"}
                ],
                validation_criteria=[
                    EnhancedValidationCriteria(
                        expected_stage_keywords={"INITIAL_INTEREST": ["using", "love"], 
                                               "PURCHASE_INTENT": ["want to order"],
                                               "PURCHASE_CONFIRMATION": ["ready to buy", "complete the purchase"]},
                        stage_progression_required=True,
                        purchase_intent_triggers=["want to order"],
                        purchase_confirmation_triggers=["ready to buy", "complete the purchase"],
                        min_response_length=60,
                        max_response_length=280,
                        required_tone="friendly",
                        must_include_keywords=["purchase", "order"],
                        min_product_matches=1,
                        max_response_time=6.0
                    )
                ],
                success_threshold=0.90,
                focus_areas=["purchase_completion", "handover_logic"]
            )
        ]

    async def run_enhanced_tests(self) -> Dict[str, Any]:
        """Run enhanced tests targeting specific failure points."""
        logger.info("🚀 Starting Enhanced Multi-Scenario Test Suite")
        
        all_results = []
        scenario_summaries = []
        
        for scenario in self.scenarios:
            logger.info(f"\n📋 Running scenario: {scenario.name}")
            
            # Run multiple iterations for consistency
            scenario_results = []
            for iteration in range(3):  # 3 iterations for reliability
                logger.info(f"  Iteration {iteration + 1}/3")
                result = await self._run_single_scenario(scenario, iteration)
                scenario_results.append(result)
                
                # Short delay between iterations
                await asyncio.sleep(1)
            
            # Analyze scenario results
            scenario_summary = self._analyze_scenario_results(scenario, scenario_results)
            scenario_summaries.append(scenario_summary)
            all_results.extend(scenario_results)
            
            logger.info(f"✅ Scenario {scenario.name} completed: {scenario_summary['success_rate']:.1%} success")

        # Generate comprehensive analysis
        comprehensive_analysis = self._generate_comprehensive_analysis(scenario_summaries)
        
        # Save results
        timestamp = int(time.time())
        results_file = f"enhanced_test_results_{timestamp}.json"
        
        with open(results_file, 'w') as f:
            json.dump({
                'test_metadata': {
                    'timestamp': datetime.now().isoformat(),
                    'test_type': 'enhanced_multi_scenario',
                    'total_scenarios': len(self.scenarios),
                    'total_iterations': len(all_results),
                    'focus_areas': ['stage_detection', 'purchase_readiness', 'response_quality']
                },
                'scenario_summaries': scenario_summaries,
                'comprehensive_analysis': comprehensive_analysis,
                'detailed_results': all_results
            }, f, indent=2)
        
        logger.info(f"📊 Enhanced test results saved to {results_file}")
        return comprehensive_analysis

    async def _run_single_scenario(self, scenario: EnhancedTestScenario, iteration: int) -> Dict[str, Any]:
        """Run a single scenario iteration."""
        conversation_id = f"{scenario.name}_{iteration}_{int(time.time())}"
        results = []
        
        for step_idx, step in enumerate(scenario.conversation_flow):
            if step['role'] == 'customer':
                start_time = time.time()
                
                # Send message to API
                response = self.client.post(
                    "/api/webhook",
                    json={
                        "sender": conversation_id,
                        "recipient": "test_page",
                        "text": step['message']
                    }
                )
                
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    response_data = response.json()
                    
                    # Enhanced validation
                    validation_result = self._enhanced_validate_response(
                        step['message'], 
                        response_data, 
                        scenario.validation_criteria[min(step_idx, len(scenario.validation_criteria) - 1)],
                        response_time
                    )
                    
                    results.append({
                        'step': step_idx,
                        'message': step['message'],
                        'response': response_data,
                        'response_time': response_time,
                        'validation': validation_result
                    })
                else:
                    results.append({
                        'step': step_idx,
                        'message': step['message'],
                        'response': None,
                        'response_time': response_time,
                        'validation': {'passed': False, 'error': f"HTTP {response.status_code}"}
                    })
                
                # Small delay between messages
                await asyncio.sleep(0.5)
        
        return {
            'scenario_name': scenario.name,
            'iteration': iteration,
            'conversation_id': conversation_id,
            'results': results,
            'overall_success': all(r['validation']['passed'] for r in results)
        }

    def _enhanced_validate_response(self, 
                                  user_message: str, 
                                  response_data: Dict[str, Any], 
                                  criteria: EnhancedValidationCriteria,
                                  response_time: float) -> Dict[str, Any]:
        """Enhanced response validation with detailed criteria checking."""
        validation_result = {
            'passed': True,
            'score': 0.0,
            'details': {},
            'failures': []
        }
        
        response_text = response_data.get('response_text', '')
        sales_stage = response_data.get('sales_stage', '')
        is_ready = response_data.get('is_ready', False)
        interested_products = response_data.get('interested_product_ids', [])
        
        # 1. Stage Detection Validation (Weight: 30%)
        stage_score = 0.0
        expected_stages = criteria.expected_stage_keywords.get(sales_stage, [])
        
        if expected_stages:
            # Check if user message contains expected triggers for this stage
            user_lower = user_message.lower()
            matching_keywords = [kw for kw in expected_stages if kw in user_lower]
            
            if matching_keywords:
                stage_score = 1.0
                validation_result['details']['stage_detection'] = 'PASS'
            else:
                # Check if stage progression makes sense
                if criteria.stage_progression_required:
                    stage_score = 0.5 if sales_stage != 'ERROR' else 0.0
                else:
                    stage_score = 0.7  # Partial credit
                validation_result['details']['stage_detection'] = 'PARTIAL'
                validation_result['failures'].append(f"Stage {sales_stage} not clearly indicated by message keywords")
        else:
            validation_result['failures'].append(f"Unexpected stage: {sales_stage}")
        
        # 2. Purchase Readiness Validation (Weight: 25%)
        readiness_score = 0.0
        user_lower = user_message.lower()
        
        # Check for purchase intent triggers
        has_intent_triggers = any(trigger in user_lower for trigger in criteria.purchase_intent_triggers)
        has_confirmation_triggers = any(trigger in user_lower for trigger in criteria.purchase_confirmation_triggers)
        
        if has_confirmation_triggers and is_ready and sales_stage == 'PURCHASE_CONFIRMATION':
            readiness_score = 1.0
            validation_result['details']['purchase_readiness'] = 'PERFECT'
        elif has_intent_triggers and sales_stage in ['PURCHASE_INTENT', 'PURCHASE_CONFIRMATION']:
            readiness_score = 0.8
            validation_result['details']['purchase_readiness'] = 'GOOD'
        elif not (has_intent_triggers or has_confirmation_triggers) and not is_ready:
            readiness_score = 1.0
            validation_result['details']['purchase_readiness'] = 'CORRECT_NOT_READY'
        else:
            readiness_score = 0.3
            validation_result['details']['purchase_readiness'] = 'MISMATCH'
            validation_result['failures'].append(f"Purchase readiness mismatch: ready={is_ready}, stage={sales_stage}")
        
        # 3. Response Quality Validation (Weight: 20%)
        quality_score = 0.0
        
        # Length check
        if criteria.min_response_length <= len(response_text) <= criteria.max_response_length:
            quality_score += 0.3
        else:
            validation_result['failures'].append(f"Response length {len(response_text)} outside range [{criteria.min_response_length}, {criteria.max_response_length}]")
        
        # Keyword inclusion/exclusion
        if criteria.must_include_keywords:
            included = sum(1 for kw in criteria.must_include_keywords if kw.lower() in response_text.lower())
            quality_score += 0.4 * (included / len(criteria.must_include_keywords))
        else:
            quality_score += 0.4
        
        if criteria.must_avoid_keywords:
            avoided = sum(1 for kw in criteria.must_avoid_keywords if kw.lower() not in response_text.lower())
            quality_score += 0.3 * (avoided / len(criteria.must_avoid_keywords))
        else:
            quality_score += 0.3
        
        validation_result['details']['response_quality'] = quality_score
        
        # 4. Product Matching Validation (Weight: 15%)
        product_score = 0.0
        
        if criteria.min_product_matches <= len(interested_products):
            product_score = 1.0
            validation_result['details']['product_matching'] = 'PASS'
        else:
            product_score = 0.5
            validation_result['details']['product_matching'] = 'INSUFFICIENT'
            validation_result['failures'].append(f"Found {len(interested_products)} products, needed {criteria.min_product_matches}")
        
        # 5. Performance Validation (Weight: 10%)
        performance_score = 1.0 if response_time <= criteria.max_response_time else 0.5
        validation_result['details']['performance'] = f"{response_time:.2f}s"
        
        if response_time > criteria.max_response_time:
            validation_result['failures'].append(f"Response time {response_time:.2f}s exceeded limit {criteria.max_response_time}s")
        
        # Calculate overall score
        total_score = (
            stage_score * 0.30 +
            readiness_score * 0.25 +
            quality_score * 0.20 +
            product_score * 0.15 +
            performance_score * 0.10
        )
        
        validation_result['score'] = total_score
        validation_result['passed'] = total_score >= criteria.consistency_threshold and len(validation_result['failures']) == 0
        
        return validation_result

    def _analyze_scenario_results(self, scenario: EnhancedTestScenario, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze results for a specific scenario."""
        total_iterations = len(results)
        successful_iterations = sum(1 for r in results if r['overall_success'])
        
        # Collect all step results
        all_step_results = []
        for result in results:
            all_step_results.extend(result['results'])
        
        # Calculate metrics
        response_times = [r['response_time'] for r in all_step_results if 'response_time' in r]
        validation_scores = [r['validation']['score'] for r in all_step_results if 'validation' in r and 'score' in r['validation']]
        
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        avg_validation_score = sum(validation_scores) / len(validation_scores) if validation_scores else 0
        
        # Identify common failure patterns
        failure_patterns = {}
        for result in all_step_results:
            if 'validation' in result and 'failures' in result['validation']:
                for failure in result['validation']['failures']:
                    failure_patterns[failure] = failure_patterns.get(failure, 0) + 1
        
        return {
            'scenario_name': scenario.name,
            'customer_type': scenario.customer_type,
            'focus_areas': scenario.focus_areas,
            'success_rate': successful_iterations / total_iterations,
            'iterations_run': total_iterations,
            'successful_iterations': successful_iterations,
            'avg_response_time': avg_response_time,
            'avg_validation_score': avg_validation_score,
            'meets_threshold': successful_iterations / total_iterations >= scenario.success_threshold,
            'common_failures': sorted(failure_patterns.items(), key=lambda x: x[1], reverse=True)[:3],
            'performance_consistency': self._calculate_consistency(response_times)
        }

    def _calculate_consistency(self, values: List[float]) -> float:
        """Calculate consistency score for a list of values."""
        if len(values) < 2:
            return 1.0
        
        avg = sum(values) / len(values)
        variance = sum((x - avg) ** 2 for x in values) / len(values)
        
        # Convert to consistency score (lower variance = higher consistency)
        consistency = 1.0 / (1.0 + variance)
        return consistency

    def _generate_comprehensive_analysis(self, scenario_summaries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate comprehensive analysis across all scenarios."""
        total_scenarios = len(scenario_summaries)
        successful_scenarios = sum(1 for s in scenario_summaries if s['meets_threshold'])
        
        overall_success_rate = sum(s['success_rate'] for s in scenario_summaries) / total_scenarios
        overall_response_time = sum(s['avg_response_time'] for s in scenario_summaries) / total_scenarios
        overall_validation_score = sum(s['avg_validation_score'] for s in scenario_summaries) / total_scenarios
        
        # Identify improvement areas
        improvement_areas = []
        
        # Stage detection improvements needed
        stage_detection_scenarios = [s for s in scenario_summaries if 'stage_detection' in s.get('focus_areas', [])]
        if stage_detection_scenarios:
            avg_stage_success = sum(s['success_rate'] for s in stage_detection_scenarios) / len(stage_detection_scenarios)
            if avg_stage_success < 0.8:
                improvement_areas.append("Stage Detection Logic")
        
        # Purchase readiness improvements needed
        purchase_scenarios = [s for s in scenario_summaries if 'purchase_readiness' in s.get('focus_areas', [])]
        if purchase_scenarios:
            avg_purchase_success = sum(s['success_rate'] for s in purchase_scenarios) / len(purchase_scenarios)
            if avg_purchase_success < 0.8:
                improvement_areas.append("Purchase Readiness Detection")
        
        # Response time improvements needed
        slow_scenarios = [s for s in scenario_summaries if s['avg_response_time'] > 7.0]
        if slow_scenarios:
            improvement_areas.append("Response Time Optimization")
        
        return {
            'overall_success_rate': overall_success_rate,
            'scenarios_meeting_threshold': successful_scenarios,
            'total_scenarios': total_scenarios,
            'avg_response_time': overall_response_time,
            'avg_validation_score': overall_validation_score,
            'improvement_areas': improvement_areas,
            'recommendation': self._generate_recommendations(scenario_summaries),
            'test_summary': {
                'enhanced_testing': True,
                'targeted_failure_points': True,
                'production_ready': overall_success_rate >= 0.8 and overall_response_time <= 7.0
            }
        }

    def _generate_recommendations(self, scenario_summaries: List[Dict[str, Any]]) -> List[str]:
        """Generate specific recommendations based on test results."""
        recommendations = []
        
        # Analyze each scenario for specific recommendations
        for summary in scenario_summaries:
            if not summary['meets_threshold']:
                scenario_name = summary['scenario_name']
                common_failures = summary.get('common_failures', [])
                
                if 'Stage_Detection' in scenario_name and common_failures:
                    recommendations.append(f"Improve stage detection logic for {scenario_name}: {common_failures[0][0]}")
                
                if 'Quick_Buyer' in scenario_name:
                    recommendations.append("Optimize quick purchase flow with faster stage transitions")
                
                if 'Hesitant_Customer' in scenario_name:
                    recommendations.append("Enhance trust-building and concern-addressing responses")
                
                if summary['avg_response_time'] > 7.0:
                    recommendations.append(f"Optimize response generation for {scenario_name} (currently {summary['avg_response_time']:.1f}s)")
        
        # General recommendations
        overall_success = sum(s['success_rate'] for s in scenario_summaries) / len(scenario_summaries)
        if overall_success < 0.8:
            recommendations.append("Consider additional training data for edge cases")
        
        if not recommendations:
            recommendations.append("System performing well - consider expanding test scenarios for edge cases")
        
        return recommendations[:5]  # Top 5 recommendations

async def main():
    """Main test execution."""
    tester = EnhancedMultiScenarioTester()
    results = await tester.run_enhanced_tests()
    
    print("\n" + "="*60)
    print("🎯 ENHANCED TEST RESULTS SUMMARY")
    print("="*60)
    print(f"Overall Success Rate: {results['overall_success_rate']:.1%}")
    print(f"Scenarios Passing: {results['scenarios_meeting_threshold']}/{results['total_scenarios']}")
    print(f"Average Response Time: {results['avg_response_time']:.2f}s")
    print(f"Average Validation Score: {results['avg_validation_score']:.2f}")
    print(f"Production Ready: {'✅ YES' if results['test_summary']['production_ready'] else '❌ NO'}")
    
    if results['improvement_areas']:
        print(f"\n🔧 Areas Needing Improvement:")
        for area in results['improvement_areas']:
            print(f"  • {area}")
    
    if results['recommendation']:
        print(f"\n💡 Recommendations:")
        for rec in results['recommendation']:
            print(f"  • {rec}")
    
    return results

if __name__ == "__main__":
    asyncio.run(main())
