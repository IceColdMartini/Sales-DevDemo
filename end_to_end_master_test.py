#!/usr/bin/env python3
"""
End-to-End Master Test Script
============================

Comprehensive integration test for the entire conversation system.
Tests the complete flow from webhook API to routing agent handover.

This script tests:
1. Webhook API endpoint functionality
2. Complete conversation flow through sales funnel
3. Product matching and recommendations
4. Sales stage progression and purchase intent detection
5. Explicit purchase confirmation handling
6. isReady flag management
7. Routing agent handover with product details
"""

import asyncio
import json
import logging
import sys
import time
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
import httpx
import uvicorn
from fastapi import FastAPI
from fastapi.testclient import TestClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import application components
sys.path.append('/Users/Kazi/Desktop/Sales-DevDemo')

from main import app
from app.models.schemas import Message, ApiResponse
from app.services.conversation_backbone import conversation_backbone
from app.core.config import settings

class ConversationTestSuite:
    """
    Comprehensive test suite for the conversation system.
    Tests end-to-end functionality from webhook to routing agent handover.
    """

    def __init__(self):
        self.client = TestClient(app)
        self.test_sender_id = f"test_user_{int(time.time())}"
        self.conversation_history = []
        self.logger = logging.getLogger(__name__)

    async def run_complete_test_suite(self) -> Dict[str, Any]:
        """
        Run the complete end-to-end test suite.

        Returns:
            Dict containing test results and analysis
        """
        self.logger.info("🚀 Starting End-to-End Master Test Suite")
        self.logger.info("=" * 60)

        test_results = {
            "test_timestamp": datetime.now(timezone.utc).isoformat(),
            "sender_id": self.test_sender_id,
            "tests": {},
            "overall_status": "pending",
            "conversation_flow": [],
            "final_handover": None
        }

        try:
            # Test 1: Initial Contact and Product Discovery
            self.logger.info("\n📋 Test 1: Initial Contact and Product Discovery")
            initial_test = await self.test_initial_contact()
            test_results["tests"]["initial_contact"] = initial_test

            # Test 2: Product Recommendations and Interest
            self.logger.info("\n📋 Test 2: Product Recommendations and Interest")
            product_test = await self.test_product_discovery()
            test_results["tests"]["product_discovery"] = product_test

            # Test 3: Price Evaluation and Comparison
            self.logger.info("\n📋 Test 3: Price Evaluation and Comparison")
            price_test = await self.test_price_evaluation()
            test_results["tests"]["price_evaluation"] = price_test

            # Test 4: Purchase Intent Development
            self.logger.info("\n📋 Test 4: Purchase Intent Development")
            intent_test = await self.test_purchase_intent()
            test_results["tests"]["purchase_intent"] = intent_test

            # Test 5: Explicit Purchase Confirmation
            self.logger.info("\n📋 Test 5: Explicit Purchase Confirmation")
            confirmation_test = await self.test_purchase_confirmation()
            test_results["tests"]["purchase_confirmation"] = confirmation_test

            # Test 6: Routing Agent Handover
            self.logger.info("\n📋 Test 6: Routing Agent Handover")
            handover_test = await self.test_routing_handover()
            test_results["tests"]["routing_handover"] = handover_test

            # Analyze overall results
            test_results["overall_status"] = self._analyze_overall_results(test_results)
            test_results["conversation_flow"] = self.conversation_history
            test_results["final_handover"] = handover_test.get("handover_data")

            self.logger.info(f"\n🎯 Test Suite Complete: {test_results['overall_status']}")

        except Exception as e:
            self.logger.error(f"❌ Test suite failed: {e}")
            test_results["overall_status"] = "failed"
            test_results["error"] = str(e)

        return test_results

    async def test_initial_contact(self) -> Dict[str, Any]:
        """Test initial customer contact and greeting."""
        try:
            # Send initial greeting message
            message_data = {
                "sender": self.test_sender_id,
                "recipient": "page_123",
                "text": "Hi there! I'm looking for some skincare products."
            }

            response = self.client.post("/api/webhook", json=message_data)
            response_data = response.json()

            # Validate response structure
            required_fields = ["sender", "response_text", "is_ready", "conversation_stage"]
            missing_fields = [field for field in required_fields if field not in response_data]

            if missing_fields:
                return {
                    "status": "failed",
                    "error": f"Missing required fields: {missing_fields}",
                    "response": response_data
                }

            # Check conversation stage
            expected_stage = "INITIAL_INTEREST"
            actual_stage = response_data.get("conversation_stage")

            # Store conversation data
            self.conversation_history.append({
                "step": "initial_contact",
                "user_message": message_data["text"],
                "ai_response": response_data.get("response_text"),
                "stage": actual_stage,
                "is_ready": response_data.get("is_ready"),
                "timestamp": datetime.utcnow().isoformat()
            })

            return {
                "status": "passed",
                "stage": actual_stage,
                "is_ready": response_data.get("is_ready"),
                "response_length": len(response_data.get("response_text", "")),
                "has_recommendations": len(response_data.get("interested_product_ids", [])) > 0
            }

        except Exception as e:
            return {
                "status": "failed",
                "error": str(e)
            }

    async def test_product_discovery(self) -> Dict[str, Any]:
        """Test product discovery and recommendations."""
        try:
            # Send product interest message
            message_data = {
                "sender": self.test_sender_id,
                "recipient": "page_123",
                "text": "I'm interested in anti-aging creams and vitamin C serums. What do you recommend?"
            }

            response = self.client.post("/api/webhook", json=message_data)
            response_data = response.json()

            # Store conversation data
            self.conversation_history.append({
                "step": "product_discovery",
                "user_message": message_data["text"],
                "ai_response": response_data.get("response_text"),
                "stage": response_data.get("conversation_stage"),
                "is_ready": response_data.get("is_ready"),
                "product_ids": response_data.get("interested_product_ids", []),
                "timestamp": datetime.utcnow().isoformat()
            })

            # Validate product recommendations
            product_ids = response_data.get("interested_product_ids", [])
            response_text = response_data.get("response_text", "").lower()

            # Check if response mentions products or recommendations
            has_product_mentions = any(keyword in response_text for keyword in [
                "cream", "serum", "recommend", "suggest", "product"
            ])

            return {
                "status": "passed",
                "stage": response_data.get("conversation_stage"),
                "is_ready": response_data.get("is_ready"),
                "product_count": len(product_ids),
                "has_product_mentions": has_product_mentions,
                "response_quality": "good" if has_product_mentions and len(response_text) > 50 else "needs_improvement"
            }

        except Exception as e:
            return {
                "status": "failed",
                "error": str(e)
            }

    async def test_price_evaluation(self) -> Dict[str, Any]:
        """Test price evaluation and comparison."""
        try:
            # Send price inquiry
            message_data = {
                "sender": self.test_sender_id,
                "recipient": "page_123",
                "text": "How much do these products cost? Are there any discounts available?"
            }

            response = self.client.post("/api/webhook", json=message_data)
            response_data = response.json()

            # Store conversation data
            self.conversation_history.append({
                "step": "price_evaluation",
                "user_message": message_data["text"],
                "ai_response": response_data.get("response_text"),
                "stage": response_data.get("conversation_stage"),
                "is_ready": response_data.get("is_ready"),
                "timestamp": datetime.utcnow().isoformat()
            })

            # Analyze response for price information
            response_text = response_data.get("response_text", "").lower()

            # Check for price-related keywords
            price_keywords = ["price", "cost", "discount", "sale", "$", "budget"]
            has_price_info = any(keyword in response_text for keyword in price_keywords)

            return {
                "status": "passed",
                "stage": response_data.get("conversation_stage"),
                "is_ready": response_data.get("is_ready"),
                "has_price_info": has_price_info,
                "stage_progression": "PRICE_EVALUATION" in str(response_data.get("conversation_stage", ""))
            }

        except Exception as e:
            return {
                "status": "failed",
                "error": str(e)
            }

    async def test_purchase_intent(self) -> Dict[str, Any]:
        """Test purchase intent development."""
        try:
            # Send purchase interest message
            message_data = {
                "sender": self.test_sender_id,
                "recipient": "page_123",
                "text": "These products sound great! I'm definitely interested in buying them."
            }

            response = self.client.post("/api/webhook", json=message_data)
            response_data = response.json()

            # Store conversation data
            self.conversation_history.append({
                "step": "purchase_intent",
                "user_message": message_data["text"],
                "ai_response": response_data.get("response_text"),
                "stage": response_data.get("conversation_stage"),
                "is_ready": response_data.get("is_ready"),
                "timestamp": datetime.utcnow().isoformat()
            })

            # Check for purchase intent detection
            response_text = response_data.get("response_text", "").lower()
            stage = str(response_data.get("conversation_stage", ""))

            # Look for confirmation language
            confirmation_keywords = ["great", "excellent", "confirm", "ready", "purchase", "buy"]
            has_confirmation = any(keyword in response_text for keyword in confirmation_keywords)

            return {
                "status": "passed",
                "stage": stage,
                "is_ready": response_data.get("is_ready"),
                "has_confirmation": has_confirmation,
                "intent_detected": "PURCHASE_INTENT" in stage or "CONFIRMATION" in stage
            }

        except Exception as e:
            return {
                "status": "failed",
                "error": str(e)
            }

    async def test_purchase_confirmation(self) -> Dict[str, Any]:
        """Test explicit purchase confirmation."""
        try:
            # Send explicit confirmation
            message_data = {
                "sender": self.test_sender_id,
                "recipient": "page_123",
                "text": "Yes, I want to buy the Vitamin C Serum and the Anti-Aging Cream. Please proceed with the purchase."
            }

            response = self.client.post("/api/webhook", json=message_data)
            response_data = response.json()

            # Store conversation data
            self.conversation_history.append({
                "step": "purchase_confirmation",
                "user_message": message_data["text"],
                "ai_response": response_data.get("response_text"),
                "stage": response_data.get("conversation_stage"),
                "is_ready": response_data.get("is_ready"),
                "product_ids": response_data.get("interested_product_ids", []),
                "timestamp": datetime.utcnow().isoformat()
            })

            # Check if isReady flag is set
            is_ready = response_data.get("is_ready", False)
            stage = str(response_data.get("conversation_stage", ""))

            # Check for handover language
            response_text = response_data.get("response_text", "").lower()
            handover_keywords = ["transfer", "handover", "agent", "representative", "assist"]
            has_handover = any(keyword in response_text for keyword in handover_keywords)

            return {
                "status": "passed",
                "stage": stage,
                "is_ready": is_ready,
                "ready_flag_set": is_ready,
                "has_handover_language": has_handover,
                "confirmation_stage": "PURCHASE_CONFIRMATION" in stage,
                "product_ids_count": len(response_data.get("interested_product_ids", []))
            }

        except Exception as e:
            return {
                "status": "failed",
                "error": str(e)
            }

    async def test_routing_handover(self) -> Dict[str, Any]:
        """Test routing agent handover with product details."""
        try:
            # Get final conversation status
            status_response = self.client.get(f"/api/webhook/status/{self.test_sender_id}")
            status_data = status_response.json()

            # Get conversation insights
            insights_response = self.client.get(f"/api/webhook/insights/{self.test_sender_id}")
            insights_data = insights_response.json()

            # Get product recommendations
            recommendations_response = self.client.get(f"/api/webhook/recommendations/{self.test_sender_id}")
            recommendations_data = recommendations_response.json()

            # Prepare handover data
            handover_data = {
                "sender_id": self.test_sender_id,
                "conversation_status": status_data.get("status"),
                "insights": insights_data.get("insights"),
                "recommendations": recommendations_data.get("recommendations", []),
                "final_stage": self.conversation_history[-1]["stage"] if self.conversation_history else None,
                "is_ready": self.conversation_history[-1]["is_ready"] if self.conversation_history else False,
                "product_ids": self.conversation_history[-1].get("product_ids", []) if self.conversation_history else [],
                "conversation_summary": self._generate_conversation_summary(),
                "handover_timestamp": datetime.utcnow().isoformat()
            }

            return {
                "status": "passed",
                "handover_data": handover_data,
                "has_product_details": len(handover_data.get("product_ids", [])) > 0,
                "is_ready_for_handover": handover_data.get("is_ready", False),
                "conversation_length": len(self.conversation_history),
                "final_stage": handover_data.get("final_stage")
            }

        except Exception as e:
            return {
                "status": "failed",
                "error": str(e)
            }

    def _generate_conversation_summary(self) -> str:
        """Generate a summary of the conversation for handover."""
        if not self.conversation_history:
            return "No conversation history available"

        summary_parts = []
        for entry in self.conversation_history:
            summary_parts.append(f"Step: {entry['step']}")
            summary_parts.append(f"User: {entry['user_message'][:100]}...")
            summary_parts.append(f"AI: {entry['ai_response'][:100]}...")
            summary_parts.append(f"Stage: {entry['stage']}, Ready: {entry['is_ready']}")
            summary_parts.append("---")

        return "\n".join(summary_parts)

    def _analyze_overall_results(self, test_results: Dict[str, Any]) -> str:
        """Analyze overall test results."""
        tests = test_results.get("tests", {})

        # Check if all critical tests passed
        critical_tests = ["initial_contact", "product_discovery", "purchase_confirmation"]
        critical_passed = all(
            tests.get(test, {}).get("status") == "passed"
            for test in critical_tests
        )

        # Check if conversation progressed through stages
        stages_progressed = len(set(
            entry["stage"] for entry in self.conversation_history
            if entry.get("stage")
        )) > 1

        # Check if isReady flag was set
        final_ready = self.conversation_history[-1]["is_ready"] if self.conversation_history else False

        if critical_passed and stages_progressed and final_ready:
            return "excellent"
        elif critical_passed and stages_progressed:
            return "good"
        elif critical_passed:
            return "fair"
        else:
            return "needs_improvement"

async def main():
    """Main test execution function."""
    print("🎯 End-to-End Conversation System Master Test")
    print("=" * 50)

    # Initialize test suite
    test_suite = ConversationTestSuite()

    # Run complete test suite
    results = await test_suite.run_complete_test_suite()

    # Print results summary
    print("\n📊 Test Results Summary")
    print("=" * 30)

    print(f"Overall Status: {results['overall_status'].upper()}")
    print(f"Test Sender ID: {results['sender_id']}")
    print(f"Conversation Steps: {len(results['conversation_flow'])}")

    print("\n🔍 Individual Test Results:")
    for test_name, test_result in results['tests'].items():
        status = test_result.get('status', 'unknown')
        status_icon = "✅" if status == "passed" else "❌" if status == "failed" else "⚠️"
        print(f"  {status_icon} {test_name}: {status}")

    # Print conversation flow
    print("\n💬 Conversation Flow:")
    for i, step in enumerate(results['conversation_flow'], 1):
        print(f"  {i}. {step['step']} → Stage: {step['stage']}, Ready: {step['is_ready']}")

    # Print handover data
    if results.get('final_handover'):
        handover = results['final_handover']
        print("\n🔄 Routing Agent Handover Data:")
        print(f"  Ready for Handover: {handover.get('is_ready_for_handover', False)}")
        print(f"  Product IDs: {handover.get('product_ids', [])}")
        print(f"  Final Stage: {handover.get('final_stage')}")
        print(f"  Conversation Length: {handover.get('conversation_length', 0)} steps")

    # Save detailed results
    results_file = f"/Users/Kazi/Desktop/Sales-DevDemo/test_results_{int(time.time())}.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\n💾 Detailed results saved to: {results_file}")

    # Return exit code based on results
    if results['overall_status'] in ['excellent', 'good']:
        print("\n🎉 SUCCESS: Conversation system is working properly!")
        return 0
    else:
        print("\n⚠️  WARNING: Some tests need attention.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
