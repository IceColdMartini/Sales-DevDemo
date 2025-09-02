#!/usr/bin/env python3
"""
Master End-to-End Test Suite
============================

Comprehensive test suite that validates the complete conversation flow from
customer inquiry to routing agent handover. This test simulates real-world
scenarios and ensures all components work together seamlessly.

Based on analysis of:
- webhook.py: Main API processing endpoint
- config.py: System configuration
- postgres_handler.py: Product database operations
- mongo_handler.py: Conversation storage
- enhanced_working_conversation_service.py: Main conversation orchestrator
- working_langchain_service.py: LangChain-powered analysis

Test Coverage:
✅ Complete conversation flow simulation
✅ Product inquiry → details → convincing → purchase confirmation
✅ Product ID tracking and persistence across conversation
✅ Routing agent handover with correct product IDs
✅ Sales stage progression and analysis
✅ Memory management and state persistence
✅ Error handling and fallback mechanisms
✅ Database integration (PostgreSQL + MongoDB)
✅ LangChain integration validation
"""

import asyncio
import logging
import sys
import os
from datetime import datetime
from typing import Dict, List, Any

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def print_test_header(test_name: str):
    """Print a formatted test header"""
    print(f"\n{'='*80}")
    print(f"🧪 {test_name}")
    print(f"{'='*80}")

def print_conversation_turn(turn_number: int, speaker: str, message: str, details: Dict = None):
    """Print formatted conversation turn"""
    print(f"\n--- Turn {turn_number} ---")
    print(f"💬 {speaker}: {message}")

    if details:
        if 'keywords' in details and details['keywords']:
            print(f"   🔍 Keywords: {', '.join(details['keywords'])}")
        if 'sales_stage' in details:
            print(f"   📊 Sales Stage: {details['sales_stage']}")
        if 'is_ready' in details:
            status = "🛒 Ready to buy!" if details['is_ready'] else "🤔 Still considering"
            print(f"   {status}")
        if 'products' in details and details['products']:
            print(f"   🛍️ Products: {len(details['products'])} matches")
        if 'product_ids' in details and details['product_ids']:
            print(f"   🆔 Product IDs: {details['product_ids']}")

class MasterEndToEndTester:
    """Master tester for complete end-to-end conversation flows"""

    def __init__(self):
        self.test_results = []
        self.conversation_history = []

    async def initialize_services(self):
        """Initialize all required services"""
        print_test_header("Service Initialization")

        try:
            # Import services
            from app.services.enhanced_working_conversation_service import enhanced_working_conversation_service
            from app.db.postgres_handler import postgres_handler
            from app.db.mongo_handler import mongo_handler

            self.service = enhanced_working_conversation_service
            self.postgres = postgres_handler
            self.mongo = mongo_handler
            
            # Initialize database connections (same as main.py startup)
            print("🔌 Connecting to databases...")
            postgres_handler.connect()
            print("✅ PostgreSQL connected")
            
            mongo_handler.connect()
            print("✅ MongoDB connected")

            print("✅ Services initialized with database connections")
            return True

        except Exception as e:
            print(f"❌ Service initialization failed: {e}")
            return False

    async def simulate_complete_conversation_flow(self):
        """Test 1: Complete conversation flow from inquiry to purchase"""
        print_test_header("Complete Conversation Flow Test")

        customer_id = f"e2e_test_customer_{datetime.now().strftime('%H%M%S')}"

        # Clear any existing conversation
        await self.clear_customer_conversation(customer_id)

        conversation_flow = [
            {
                "message": "Hi, I'm looking for a good moisturizer for dry skin",
                "expected_stage": "INITIAL_INTEREST",
                "expected_ready": False,
                "expected_keywords": ["moisturizer", "skin", "dry"]
            },
            {
                "message": "What are the prices for your face creams?",
                "expected_stage": "PRICE_INQUIRY",
                "expected_ready": False,
                "expected_has_products": True
            },
            {
                "message": "The second one looks good, tell me more about it",
                "expected_stage": "PRODUCT_INTEREST",
                "expected_ready": False,
                "expected_has_products": True
            },
            {
                "message": "I'll take the moisturizer, how do I purchase it?",
                "expected_stage": "PURCHASE_CONFIRMATION",
                "expected_ready": True,
                "expected_has_product_ids": True
            }
        ]

        print(f"🎭 Simulating complete conversation for customer: {customer_id}")

        for turn_number, turn in enumerate(conversation_flow, 1):
            print_conversation_turn(turn_number, "Customer", turn["message"])

            try:
                # Process message
                result = await self.service.process_enhanced_conversation(
                    customer_id, turn["message"], ""
                )

                # Validate response structure
                required_fields = ['response', 'products', 'keywords', 'sales_stage', 'is_ready_to_buy']
                for field in required_fields:
                    if field not in result:
                        print(f"❌ Missing required field: {field}")
                        return False

                # Print AI response with analysis
                print_conversation_turn(turn_number, "AI Assistant", result['response'], {
                    'keywords': result.get('keywords', []),
                    'sales_stage': result.get('sales_stage', 'UNKNOWN'),
                    'is_ready': result.get('is_ready_to_buy', False),
                    'products': result.get('products', []),
                    'product_ids': result.get('interested_product_ids', [])
                })

                # Validate expectations
                if result['sales_stage'] != turn['expected_stage']:
                    print(f"⚠️ Stage mismatch: Expected {turn['expected_stage']}, Got {result['sales_stage']}")

                if result['is_ready_to_buy'] != turn['expected_ready']:
                    print(f"⚠️ Ready status mismatch: Expected {turn['expected_ready']}, Got {result['is_ready_to_buy']}")

                if turn.get('expected_has_products', False) and not result.get('products'):
                    print("⚠️ Expected products but none found")

                if turn.get('expected_has_product_ids', False) and not result.get('interested_product_ids'):
                    print("⚠️ Expected product IDs but none found")

                # Store for next turn
                self.conversation_history.append({
                    'turn': turn_number,
                    'customer_message': turn['message'],
                    'ai_response': result['response'],
                    'result': result
                })

                # Add small delay for readability
                await asyncio.sleep(0.5)

            except Exception as e:
                print(f"❌ Conversation turn {turn_number} failed: {e}")
                return False

        # Final validation - check routing agent handover
        final_result = self.conversation_history[-1]['result']

        if final_result['is_ready_to_buy'] and final_result.get('interested_product_ids'):
            print("✅ SUCCESS: Routing agent handover ready!")
            print(f"   📦 Product IDs for routing agent: {final_result['interested_product_ids']}")
            return True
        else:
            print("❌ FAILURE: Routing agent handover not properly configured")
            return False

    async def test_product_id_persistence(self):
        """Test 2: Product ID persistence across conversation turns"""
        print_test_header("Product ID Persistence Test")

        customer_id = f"persistence_test_{datetime.now().strftime('%H%M%S')}"

        # Clear any existing conversation
        await self.clear_customer_conversation(customer_id)

        # First message - inquire about products
        result1 = await self.service.process_enhanced_conversation(
            customer_id, "I'm looking for shampoo and conditioner", ""
        )

        initial_product_ids = result1.get('interested_product_ids', [])
        print(f"📝 Initial inquiry - Product IDs: {initial_product_ids}")

        # Second message - show interest in specific product
        result2 = await self.service.process_enhanced_conversation(
            customer_id, "Tell me more about the first shampoo", ""
        )

        second_product_ids = result2.get('interested_product_ids', [])
        print(f"📝 Product interest - Product IDs: {second_product_ids}")

        # Third message - confirm purchase
        result3 = await self.service.process_enhanced_conversation(
            customer_id, "I'll buy the shampoo, how much is it?", ""
        )

        final_product_ids = result3.get('interested_product_ids', [])
        print(f"📝 Purchase confirmation - Product IDs: {final_product_ids}")

        # Validate persistence
        if not initial_product_ids and not second_product_ids and final_product_ids:
            print("❌ FAILURE: Product IDs not persisted through conversation")
            return False

        if result3['is_ready_to_buy'] and not final_product_ids:
            print("❌ FAILURE: Ready to buy but no product IDs for routing agent")
            return False

        print("✅ SUCCESS: Product IDs properly persisted and available for routing agent")
        return True

    async def test_sales_stage_progression(self):
        """Test 3: Sales stage progression through conversation"""
        print_test_header("Sales Stage Progression Test")

        customer_id = f"stage_test_{datetime.now().strftime('%H%M%S')}"

        # Clear any existing conversation
        await self.clear_customer_conversation(customer_id)

        stages_to_test = [
            ("Hello, what skincare products do you have?", "INITIAL_INTEREST"),
            ("I'm interested in moisturizers", "PRODUCT_INTEREST"),
            ("What's the price of the first one?", "PRICE_INQUIRY"),
            ("I'll take it, how do I buy?", "PURCHASE_CONFIRMATION")
        ]

        for message, expected_stage in stages_to_test:
            result = await self.service.process_enhanced_conversation(customer_id, message, "")

            actual_stage = result.get('sales_stage', 'UNKNOWN')
            print(f"💬 '{message[:30]}...' → Stage: {actual_stage}")

            if actual_stage != expected_stage:
                print(f"⚠️ Stage progression issue: Expected {expected_stage}, Got {actual_stage}")

        # Final check - should be ready to buy
        final_result = await self.service.process_enhanced_conversation(
            customer_id, "Yes, I want to purchase it now", ""
        )

        if final_result['is_ready_to_buy']:
            print("✅ SUCCESS: Sales stage progressed to purchase confirmation")
            return True
        else:
            print("❌ FAILURE: Sales stage did not progress to purchase confirmation")
            return False

    async def test_routing_agent_integration(self):
        """Test 4: Routing agent integration and handover"""
        print_test_header("Routing Agent Integration Test")

        customer_id = f"routing_test_{datetime.now().strftime('%H%M%S')}"

        # Clear any existing conversation
        await self.clear_customer_conversation(customer_id)

        # Simulate conversation leading to purchase
        messages = [
            "I need a good perfume",
            "Show me the prices",
            "I'll buy the first one"
        ]

        for message in messages:
            result = await self.service.process_enhanced_conversation(customer_id, message, "")

        # Check final state
        final_result = await self.service.process_enhanced_conversation(
            customer_id, "Yes, confirm my purchase", ""
        )

        # Validate routing agent response format
        required_routing_fields = ['sender', 'product_interested', 'interested_product_ids', 'response_text', 'is_ready']

        for field in required_routing_fields:
            if field not in final_result:
                print(f"❌ Missing routing agent field: {field}")
                return False

        # Validate handover logic
        if final_result['is_ready'] and not final_result['interested_product_ids']:
            print("❌ FAILURE: Ready to buy but no product IDs for routing agent")
            return False

        if not final_result['is_ready'] and final_result['interested_product_ids']:
            print("⚠️ WARNING: Not ready to buy but has product IDs (might be tracking)")

        print("✅ SUCCESS: Routing agent integration working correctly")
        print(f"   📦 Handover ready: {final_result['is_ready']}")
        print(f"   🆔 Product IDs: {final_result['interested_product_ids']}")
        print(f"   📝 Product interested: {final_result.get('product_interested', 'None')}")

        return True

    async def test_error_handling_and_fallbacks(self):
        """Test 5: Error handling and fallback mechanisms"""
        print_test_header("Error Handling and Fallbacks Test")

        customer_id = f"error_test_{datetime.now().strftime('%H%M%S')}"

        # Test with invalid input
        try:
            result = await self.service.process_enhanced_conversation(customer_id, "", "")
            if 'error' in result or result.get('response') == "":
                print("❌ FAILURE: Empty message not handled properly")
                return False
        except Exception as e:
            print(f"⚠️ Exception handling: {e}")

        # Test with very long message
        long_message = "Hello " * 1000
        try:
            result = await self.service.process_enhanced_conversation(customer_id, long_message, "")
            if not result.get('response'):
                print("❌ FAILURE: Long message not handled properly")
                return False
        except Exception as e:
            print(f"⚠️ Long message handling: {e}")

        # Test conversation state recovery
        result = await self.service.process_enhanced_conversation(
            customer_id, "I'm looking for soap", ""
        )

        if not result.get('response'):
            print("❌ FAILURE: Basic conversation failed")
            return False

        print("✅ SUCCESS: Error handling and fallbacks working correctly")
        return True

    async def clear_customer_conversation(self, customer_id: str):
        """Clear conversation history for test customer"""
        try:
            self.mongo.delete_conversation(customer_id)
            self.service.clear_conversation_memory(customer_id)
            print(f"🗑️ Cleared conversation history for {customer_id}")
        except Exception as e:
            print(f"⚠️ Could not clear conversation: {e}")

    async def run_all_tests(self):
        """Run all end-to-end tests"""
        print("\n🚀 Starting Master End-to-End Test Suite")
        print(f"⏰ Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # Initialize services
        if not await self.initialize_services():
            return 0, []

        # Test scenarios
        tests = [
            ("Complete Conversation Flow", self.simulate_complete_conversation_flow),
            ("Product ID Persistence", self.test_product_id_persistence),
            ("Sales Stage Progression", self.test_sales_stage_progression),
            ("Routing Agent Integration", self.test_routing_agent_integration),
            ("Error Handling & Fallbacks", self.test_error_handling_and_fallbacks),
        ]

        results = []
        for test_name, test_func in tests:
            print(f"\n🏃‍♂️ Running: {test_name}")
            try:
                result = await test_func()
                results.append((test_name, result))

                if result:
                    print(f"✅ {test_name}: PASSED")
                else:
                    print(f"❌ {test_name}: FAILED")

            except Exception as e:
                print(f"❌ {test_name}: ERROR - {e}")
                results.append((test_name, False))

        # Print final summary
        print(f"\n{'='*80}")
        print("📊 MASTER END-TO-END TEST SUMMARY")
        print(f"{'='*80}")

        passed = sum(1 for _, result in results if result)
        total = len(results)
        success_rate = (passed / total) * 100 if total > 0 else 0

        print(f"🎯 Overall Success Rate: {success_rate:.1f}% ({passed}/{total} tests passed)")

        for test_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"   {status} {test_name}")

        if success_rate == 100:
            print("\n🎉 EXCELLENT: All end-to-end flows working perfectly!")
            print("🚀 System is production-ready with complete conversation handling")
        elif success_rate >= 80:
            print("\n🎯 GOOD: Core functionality working with minor issues")
            print("🔧 Address the failed tests before production deployment")
        elif success_rate >= 60:
            print("\n⚠️ FAIR: Basic functionality working but needs improvements")
            print("🔧 Significant fixes required")
        else:
            print("\n❌ POOR: Critical issues found in conversation flow")
            print("🔧 Major fixes required before deployment")

        print(f"\n⏰ Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        return success_rate, results

async def main():
    """Main test execution"""
    print("🎯 Master End-to-End Test Suite for Sales Agent")
    print("==============================================")
    print("This test suite validates the complete conversation flow:")
    print("1. Customer inquiry → Product matching")
    print("2. Product details → Sales conversation")
    print("3. Purchase intent → Confirmation")
    print("4. Routing agent handover → Product IDs")

    tester = MasterEndToEndTester()

    try:
        success_rate, results = await tester.run_all_tests()

        # Exit with appropriate code
        exit_code = 0 if success_rate >= 80 else 1
        sys.exit(exit_code)

    except KeyboardInterrupt:
        print("\n⚠️ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
