"""
Focused Enhancement Validation Test
==================================

Test specific improvements we made to validate they work correctly.
"""

import asyncio
import json
import time
from datetime import datetime
from fastapi.testclient import TestClient
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_app():
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    from main import app
    return app

class FocusedEnhancementTest:
    """Test specific improvements made to the conversation system."""

    def __init__(self):
        self.client = TestClient(get_app())
        self.results = []

    def run_validation_tests(self):
        """Run focused validation tests."""
        logger.info("🎯 Starting Focused Enhancement Validation")
        
        test_scenarios = [
            {
                "name": "Stage Detection Accuracy",
                "conversation": [
                    "Hi, I'm looking for skincare products",
                    "Tell me about anti-aging serums",
                    "What's the price range?",
                    "I'd like to get the serum",
                    "Yes, I'll take it"
                ],
                "expected_stages": ["INITIAL_INTEREST", "PRODUCT_DISCOVERY", "PRICE_EVALUATION", "PURCHASE_INTENT", "PURCHASE_CONFIRMATION"]
            },
            {
                "name": "Quick Purchase Flow",
                "conversation": [
                    "I need a moisturizer under $30",
                    "That looks perfect, I'll take it",
                    "How do I buy this?"
                ],
                "expected_stages": ["INITIAL_INTEREST", "PURCHASE_CONFIRMATION", "PURCHASE_CONFIRMATION"]
            },
            {
                "name": "Product Information Extraction",
                "conversation": [
                    "I want sulfate-free cleansers with salicylic acid",
                    "Do you have CeraVe or Neutrogena brands?"
                ],
                "expected_stages": ["INITIAL_INTEREST", "PRODUCT_DISCOVERY"]
            }
        ]
        
        for scenario in test_scenarios:
            logger.info(f"\n📋 Testing: {scenario['name']}")
            result = self._test_scenario(scenario)
            self.results.append(result)
            
            # Print immediate feedback
            success_rate = result['success_rate']
            logger.info(f"✅ {scenario['name']}: {success_rate:.1%} success")
        
        # Generate summary
        self._generate_summary()

    def _test_scenario(self, scenario):
        """Test a single scenario."""
        conversation_id = f"test_{int(time.time())}"
        interactions = []
        
        for i, message in enumerate(scenario['conversation']):
            start_time = time.time()
            
            response = self.client.post(
                "/api/webhook",
                json={
                    "sender": conversation_id,
                    "recipient": "test_page",
                    "text": message
                }
            )
            
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                response_data = response.json()
                
                # Validate response
                validation = self._validate_interaction(
                    message, 
                    response_data, 
                    scenario.get('expected_stages', [None])[i] if i < len(scenario.get('expected_stages', [])) else None,
                    response_time
                )
                
                interactions.append({
                    'message': message,
                    'response': response_data,
                    'validation': validation,
                    'response_time': response_time
                })
            else:
                interactions.append({
                    'message': message,
                    'response': None,
                    'validation': {'passed': False, 'error': f"HTTP {response.status_code}"},
                    'response_time': response_time
                })
            
            # Small delay between messages
            time.sleep(0.5)
        
        # Calculate success rate
        successful = sum(1 for interaction in interactions if interaction['validation']['passed'])
        success_rate = successful / len(interactions) if interactions else 0
        
        return {
            'scenario_name': scenario['name'],
            'interactions': interactions,
            'success_rate': success_rate,
            'total_interactions': len(interactions),
            'successful_interactions': successful
        }

    def _validate_interaction(self, user_message, response_data, expected_stage, response_time):
        """Validate a single interaction."""
        validation = {'passed': True, 'details': [], 'issues': []}
        
        # Check basic response structure
        required_fields = ['response_text', 'conversation_stage', 'is_ready', 'confidence']
        for field in required_fields:
            if field not in response_data:
                validation['passed'] = False
                validation['issues'].append(f"Missing field: {field}")
            else:
                validation['details'].append(f"{field}: {response_data[field]}")
        
        # Check response quality
        response_text = response_data.get('response_text', '')
        if len(response_text) < 30:
            validation['issues'].append(f"Response too short: {len(response_text)} chars")
        elif len(response_text) > 500:
            validation['issues'].append(f"Response too long: {len(response_text)} chars")
        
        # Check stage progression if expected
        if expected_stage:
            actual_stage = response_data.get('conversation_stage')
            if actual_stage == expected_stage:
                validation['details'].append(f"✅ Stage match: {expected_stage}")
            else:
                validation['issues'].append(f"Stage mismatch: expected {expected_stage}, got {actual_stage}")
        
        # Check response time
        if response_time > 8.0:
            validation['issues'].append(f"Slow response: {response_time:.2f}s")
        else:
            validation['details'].append(f"Response time: {response_time:.2f}s")
        
        # Check purchase readiness logic
        user_lower = user_message.lower()
        is_ready = response_data.get('is_ready', False)
        
        purchase_indicators = ["i'll take", "i want to buy", "how do i buy", "purchase", "order"]
        has_purchase_intent = any(indicator in user_lower for indicator in purchase_indicators)
        
        if has_purchase_intent and not is_ready:
            validation['issues'].append("User shows purchase intent but system didn't detect readiness")
        elif not has_purchase_intent and is_ready:
            validation['issues'].append("System detected readiness without clear purchase intent")
        
        # Final validation
        if validation['issues']:
            validation['passed'] = False
        
        return validation

    def _generate_summary(self):
        """Generate test summary."""
        print("\n" + "="*60)
        print("🎯 FOCUSED ENHANCEMENT VALIDATION RESULTS")
        print("="*60)
        
        total_interactions = sum(r['total_interactions'] for r in self.results)
        successful_interactions = sum(r['successful_interactions'] for r in self.results)
        overall_success = successful_interactions / total_interactions if total_interactions > 0 else 0
        
        print(f"Overall Success Rate: {overall_success:.1%}")
        print(f"Total Interactions: {successful_interactions}/{total_interactions}")
        
        for result in self.results:
            print(f"\n📋 {result['scenario_name']}: {result['success_rate']:.1%} success")
            
            for i, interaction in enumerate(result['interactions']):
                status = "✅" if interaction['validation']['passed'] else "❌"
                message_preview = interaction['message'][:40] + "..." if len(interaction['message']) > 40 else interaction['message']
                print(f"  {status} Step {i+1}: {message_preview}")
                
                if not interaction['validation']['passed']:
                    for issue in interaction['validation']['issues']:
                        print(f"      ⚠️  {issue}")
        
        # Enhanced module performance
        print(f"\n🔧 Enhanced Module Performance:")
        response_times = []
        stages_detected = []
        
        for result in self.results:
            for interaction in result['interactions']:
                if interaction['response']:
                    response_times.append(interaction['response_time'])
                    stages_detected.append(interaction['response'].get('conversation_stage'))
        
        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
            print(f"  • Average Response Time: {avg_response_time:.2f}s")
            print(f"  • Fastest Response: {min(response_times):.2f}s")
            print(f"  • Slowest Response: {max(response_times):.2f}s")
        
        if stages_detected:
            stage_distribution = {}
            for stage in stages_detected:
                stage_distribution[stage] = stage_distribution.get(stage, 0) + 1
            
            print(f"  • Stage Distribution:")
            for stage, count in stage_distribution.items():
                print(f"    - {stage}: {count} times")
        
        # Improvement validation
        print(f"\n💡 Enhancement Validation:")
        
        if overall_success >= 0.8:
            print("  ✅ Enhanced modules are performing well")
        elif overall_success >= 0.6:
            print("  ⚠️  Enhanced modules show improvement but need refinement")
        else:
            print("  ❌ Enhanced modules need significant improvement")
        
        if avg_response_time <= 7.0:
            print("  ✅ Response time targets met")
        else:
            print("  ⚠️  Response times need optimization")
        
        # Save results
        timestamp = int(time.time())
        results_file = f"focused_validation_results_{timestamp}.json"
        
        with open(results_file, 'w') as f:
            json.dump({
                'test_metadata': {
                    'timestamp': datetime.now().isoformat(),
                    'test_type': 'focused_enhancement_validation',
                    'total_scenarios': len(self.results),
                    'overall_success_rate': overall_success
                },
                'results': self.results,
                'performance_metrics': {
                    'avg_response_time': avg_response_time if response_times else 0,
                    'stage_distribution': stage_distribution if stages_detected else {}
                }
            }, f, indent=2)
        
        print(f"\n📊 Detailed results saved to {results_file}")

if __name__ == "__main__":
    tester = FocusedEnhancementTest()
    tester.run_validation_tests()
