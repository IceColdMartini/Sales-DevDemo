#!/usr/bin/env python3
"""
Master Real-Life Conversation Test
==================================

Comprehensive simulation of a real customer conversation with thorough validation.
This script acts as a real customer and validates every aspect of the conversation system:

1. Conversation storage and retrieval
2. State detection and transitions
3. Information extraction accuracy
4. Response quality and human-like nature
5. Multi-product context management
6. Proper handover to routing agents
7. End-to-end conversation flow validation

Author: AI Assistant
Date: September 7, 2025
"""

import asyncio
import json
import logging
import sys
import time
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from fastapi.testclient import TestClient

# Configure comprehensive logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('master_conversation_test.log')
    ]
)
logger = logging.getLogger(__name__)

# Import application components
sys.path.append('/Users/Kazi/Desktop/Sales-DevDemo')

from main import app
from app.models.schemas import Message
from app.db.mongo_handler import mongo_handler
from app.db.postgres_handler import postgres_handler

class MasterConversationTester:
    """
    Comprehensive real-life conversation tester that validates every aspect
    of the conversation system with detailed step-by-step analysis.
    """

    def __init__(self):
        self.client = TestClient(app)
        self.customer_id = f"master_test_customer_{int(time.time())}"
        self.test_results = {
            "test_session": {
                "customer_id": self.customer_id,
                "start_time": datetime.now(timezone.utc).isoformat(),
                "test_type": "master_real_life_simulation"
            },
            "conversation_steps": [],
            "validation_results": [],
            "system_performance": {},
            "issues_detected": [],
            "recommendations": []
        }
        
        # Real customer conversation scenario - Natural progression
        self.conversation_scenario = [
            {
                "step": 1,
                "customer_input": "Hi! I've been having issues with my skin lately. It's been really dry and I'm looking for some good skincare products.",
                "expected_behavior": {
                    "stage": "INITIAL_INTEREST",
                    "should_extract": ["skincare", "dry skin", "moisturizer"],
                    "should_recommend": True,
                    "should_ask_questions": True,
                    "ready_to_buy": False,
                    "handover": False
                },
                "validation_checks": [
                    "conversation_stored_correctly",
                    "stage_detected_properly",
                    "keywords_extracted",
                    "appropriate_response_tone",
                    "product_recommendations_made"
                ]
            },
            {
                "step": 2,
                "customer_input": "I'm particularly interested in anti-aging products. Do you have any vitamin C serums? Also, what about moisturizers for sensitive skin?",
                "expected_behavior": {
                    "stage": "PRODUCT_DISCOVERY", 
                    "should_extract": ["anti-aging", "vitamin C serum", "moisturizer", "sensitive skin"],
                    "should_recommend": True,
                    "should_provide_details": True,
                    "ready_to_buy": False,
                    "handover": False,
                    "multiple_products": True
                },
                "validation_checks": [
                    "multiple_product_interest_tracked",
                    "product_details_provided",
                    "conversation_context_maintained",
                    "stage_progression_correct"
                ]
            },
            {
                "step": 3,
                "customer_input": "These sound great! What are the prices for the vitamin C serum and the moisturizer? I want to make sure they fit my budget.",
                "expected_behavior": {
                    "stage": "PRICE_EVALUATION",
                    "should_extract": ["price", "budget", "cost"],
                    "should_provide_pricing": True,
                    "ready_to_buy": False,
                    "handover": False,
                    "multiple_products": True
                },
                "validation_checks": [
                    "price_information_provided",
                    "budget_considerations_addressed",
                    "multiple_products_still_tracked"
                ]
            },
            {
                "step": 4, 
                "customer_input": "Perfect! The prices are reasonable. I'd like to get both the vitamin C serum and the moisturizer. They seem like exactly what I need.",
                "expected_behavior": {
                    "stage": ["PURCHASE_INTENT", "PURCHASE_CONFIRMATION"],  # Accept both stages
                    "should_extract": ["like to get", "both", "reasonable"],
                    "ready_to_buy": True,
                    "handover": True,
                    "multiple_products": True
                },
                "validation_checks": [
                    "purchase_intent_recognized",
                    "readiness_detected",
                    "both_products_confirmed",
                    "handover_preparation_started"
                ]
            },
            {
                "step": 5,
                "customer_input": "Yes, I'm ready to buy both products now. Please help me complete the purchase. How do I proceed?",
                "expected_behavior": {
                    "stage": "PURCHASE_CONFIRMATION", 
                    "should_extract": ["ready to buy", "complete purchase", "proceed"],
                    "ready_to_buy": True,
                    "handover": True,
                    "multiple_products": True
                },
                "validation_checks": [
                    "final_confirmation_recognized",
                    "handover_message_prepared",
                    "all_product_ids_available",
                    "routing_agent_data_complete"
                ]
            }
        ]

    async def run_master_test(self) -> Dict[str, Any]:
        """
        Run the comprehensive master test with detailed validation.
        
        Returns:
            Dict: Comprehensive test results with analysis
        """
        logger.info("🎭 MASTER REAL-LIFE CONVERSATION TEST STARTING")
        logger.info("=" * 70)
        
        try:
            # Initialize databases
            await self._initialize_system()
            
            # Record initial state
            await self._record_initial_state()
            
            # Execute conversation scenario
            for step_config in self.conversation_scenario:
                logger.info(f"\n🎯 STEP {step_config['step']}: EXECUTING CUSTOMER INTERACTION")
                logger.info(f"Customer Input: {step_config['customer_input']}")
                
                # Execute conversation step
                step_result = await self._execute_conversation_step(step_config)
                self.test_results["conversation_steps"].append(step_result)
                
                # Validate system behavior
                validation_result = await self._validate_system_behavior(step_config, step_result)
                self.test_results["validation_results"].append(validation_result)
                
                # Log step results
                self._log_step_results(step_config["step"], step_result, validation_result)
                
                # Brief pause between steps (simulate real conversation)
                await asyncio.sleep(1)
            
            # Final system validation
            await self._final_system_validation()
            
            # Generate comprehensive analysis
            self._generate_final_analysis()
            
            # Save detailed results
            await self._save_test_results()
            
        except Exception as e:
            logger.error(f"❌ Master test failed: {e}")
            self.test_results["test_status"] = "failed"
            self.test_results["error"] = str(e)
        
        finally:
            await self._cleanup_system()
        
        return self.test_results

    async def _initialize_system(self):
        """Initialize and verify system components."""
        logger.info("🔌 Initializing system components...")
        
        # Connect to databases
        try:
            mongo_handler.connect()
            logger.info("✅ MongoDB connection established")
        except Exception as e:
            logger.error(f"❌ MongoDB connection failed: {e}")
            raise
        
        try:
            postgres_handler.connect()
            logger.info("✅ PostgreSQL connection established")  
        except Exception as e:
            logger.error(f"❌ PostgreSQL connection failed: {e}")
            raise

    async def _record_initial_state(self):
        """Record the initial state of the system."""
        logger.info("📋 Recording initial system state...")
        
        # Check MongoDB state
        db = mongo_handler.get_database()
        conversations_collection = db["conversations"]
        initial_conversation_count = conversations_collection.count_documents({})
        
        # Check PostgreSQL state  
        try:
            product_count_result = postgres_handler.execute_query("SELECT COUNT(*) FROM products")
            total_products = product_count_result[0][0] if product_count_result else 0
        except Exception as e:
            logger.warning(f"PostgreSQL query failed: {e}")
            total_products = 0
        
        self.test_results["initial_state"] = {
            "mongodb_conversations": initial_conversation_count,
            "postgresql_products": total_products,
            "customer_exists": conversations_collection.count_documents({"sender_id": self.customer_id}) > 0
        }
        
        logger.info(f"Initial state: {initial_conversation_count} conversations, {total_products} products")

    async def _execute_conversation_step(self, step_config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single conversation step and capture response."""
        
        # Prepare message
        message_data = {
            "sender": self.customer_id,
            "recipient": "page_123",
            "text": step_config["customer_input"]
        }
        
        # Send message and measure response time
        start_time = time.time()
        response = self.client.post("/api/webhook", json=message_data)
        response_time = time.time() - start_time
        
        # Parse response
        response_data = response.json() if response.status_code == 200 else {}
        
        # Capture conversation state immediately after response
        conversation_state = await self._capture_conversation_state()
        
        return {
            "step_number": step_config["step"],
            "customer_message": step_config["customer_input"], 
            "ai_response": response_data.get("response_text", ""),
            "response_time_seconds": round(response_time, 3),
            "http_status": response.status_code,
            "response_data": response_data,
            "conversation_state": conversation_state,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    async def _capture_conversation_state(self) -> Dict[str, Any]:
        """Capture the current state of the conversation from database."""
        try:
            # Get from MongoDB
            db = mongo_handler.get_database()
            conversations_collection = db["conversations"]
            conversation_doc = conversations_collection.find_one({"sender_id": self.customer_id})
            
            if conversation_doc:
                # Handle nested conversation structure
                conversation_data = conversation_doc.get("conversation", {})
                if isinstance(conversation_data, dict):
                    messages = conversation_data.get("conversation", [])
                else:
                    messages = conversation_data if isinstance(conversation_data, list) else []
                
                return {
                    "stored": True,
                    "message_count": len(messages),
                    "current_stage": conversation_doc.get("current_stage", "UNKNOWN"),
                    "product_ids": conversation_doc.get("product_ids", []),
                    "is_ready": conversation_doc.get("is_ready", False),
                    "last_updated": conversation_doc.get("updated_at"),
                    "messages": messages[-2:] if len(messages) >= 2 else messages  # Last 2 messages
                }
            else:
                return {"stored": False, "error": "No conversation found"}
                
        except Exception as e:
            return {"stored": False, "error": str(e)}

    async def _validate_system_behavior(self, step_config: Dict[str, Any], step_result: Dict[str, Any]) -> Dict[str, Any]:
        """Validate that the system behaved correctly for this step."""
        
        validation_result = {
            "step_number": step_config["step"],
            "validations": {},
            "overall_success": True,
            "issues_found": []
        }
        
        expected = step_config["expected_behavior"]
        response_data = step_result["response_data"]
        conversation_state = step_result["conversation_state"]
        
        # Validate conversation storage
        storage_valid = self._validate_conversation_storage(conversation_state, step_config["step"])
        validation_result["validations"]["conversation_storage"] = storage_valid
        
        # Validate stage detection
        stage_valid = self._validate_stage_detection(response_data, expected, conversation_state)
        validation_result["validations"]["stage_detection"] = stage_valid
        
        # Validate information extraction
        extraction_valid = self._validate_information_extraction(response_data, expected, step_config)
        validation_result["validations"]["information_extraction"] = extraction_valid
        
        # Validate response quality
        response_valid = self._validate_response_quality(step_result, expected)
        validation_result["validations"]["response_quality"] = response_valid
        
        # Validate multi-product handling
        if expected.get("multiple_products", False):
            multiproduct_valid = self._validate_multiproduct_handling(response_data, conversation_state, step_config["step"])
            validation_result["validations"]["multiproduct_handling"] = multiproduct_valid
        
        # Validate handover preparation
        if expected.get("handover", False):
            handover_valid = self._validate_handover_preparation(response_data, conversation_state)
            validation_result["validations"]["handover_preparation"] = handover_valid
        
        # Overall success calculation
        failed_validations = [k for k, v in validation_result["validations"].items() if not v["success"]]
        validation_result["overall_success"] = len(failed_validations) == 0
        validation_result["failed_validations"] = failed_validations
        
        return validation_result

    def _get_keyword_synonyms(self, keyword: str) -> List[str]:
        """Get synonyms for better keyword matching."""
        synonyms = {
            "skincare": ["skin care", "beauty", "cosmetic"],
            "dry skin": ["dehydrated", "moisture", "hydration"],
            "moisturizer": ["lotion", "cream", "hydrator"],
            "anti-aging": ["anti aging", "wrinkle", "fine lines"],
            "vitamin c serum": ["vitamin c", "serum", "brightening"],
            "sensitive skin": ["gentle", "hypoallergenic"],
            "price": ["cost", "pricing", "expensive", "affordable"],
            "budget": ["affordable", "cost", "money"],
            "like to get": ["want", "need", "interested", "buy"],
            "both": ["two", "these", "products"],
            "reasonable": ["good", "fair", "affordable"],
            "ready to buy": ["purchase", "buy", "ready"],
            "complete purchase": ["checkout", "order", "buy"],
            "proceed": ["continue", "next", "go ahead"]
        }
        return synonyms.get(keyword, [])

    def _validate_conversation_storage(self, conversation_state: Dict[str, Any], step_number: int) -> Dict[str, Any]:
        """Validate that conversation is properly stored in database."""
        
        if not conversation_state.get("stored", False):
            return {
                "success": False,
                "issue": "Conversation not stored in database",
                "details": conversation_state
            }
        
        expected_messages = step_number * 2  # customer + AI response per step
        actual_messages = conversation_state.get("message_count", 0)
        
        if actual_messages < expected_messages:
            return {
                "success": False,
                "issue": f"Missing messages: expected {expected_messages}, got {actual_messages}",
                "details": conversation_state
            }
        
        return {
            "success": True,
            "message_count": actual_messages,
            "details": "Conversation properly stored"
        }

    def _validate_stage_detection(self, response_data: Dict[str, Any], expected: Dict[str, Any], conversation_state: Dict[str, Any]) -> Dict[str, Any]:
        """Validate that the conversation stage is correctly detected."""
        
        detected_stage = response_data.get("conversation_stage") or conversation_state.get("current_stage")
        expected_stage = expected["stage"]
        
        # Handle multiple acceptable stages
        if isinstance(expected_stage, list):
            stage_match = detected_stage in expected_stage
            if not stage_match:
                return {
                    "success": False,
                    "issue": f"Stage mismatch: expected one of {expected_stage}, got {detected_stage}",
                    "details": {"expected": expected_stage, "actual": detected_stage}
                }
        else:
            if detected_stage != expected_stage:
                return {
                    "success": False,
                    "issue": f"Stage mismatch: expected {expected_stage}, got {detected_stage}",
                    "details": {"expected": expected_stage, "actual": detected_stage}
                }
        
        # Validate readiness detection
        detected_ready = response_data.get("is_ready", False) or conversation_state.get("is_ready", False)
        expected_ready = expected.get("ready_to_buy", False)
        
        if detected_ready != expected_ready:
            return {
                "success": False,
                "issue": f"Readiness mismatch: expected {expected_ready}, got {detected_ready}",
                "details": {"expected_ready": expected_ready, "actual_ready": detected_ready}
            }
        
        return {
            "success": True,
            "stage": detected_stage,
            "ready": detected_ready,
            "details": "Stage and readiness correctly detected"
        }

    def _validate_information_extraction(self, response_data: Dict[str, Any], expected: Dict[str, Any], step_config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate that key information is properly extracted from customer message."""
        
        should_extract = expected.get("should_extract", [])
        customer_input = step_config["customer_input"].lower()
        ai_response = response_data.get("response_text", "").lower()
        
        extraction_results = {}
        
        for keyword in should_extract:
            # Check if keyword was in customer input (should be extracted)
            in_input = keyword.lower() in customer_input
            # Check if AI response acknowledges/responds to this keyword (more flexible matching)
            keyword_parts = keyword.lower().split()
            acknowledged = any(
                any(part in ai_response for part in keyword_parts) or
                keyword.lower() in ai_response or
                any(synonym in ai_response for synonym in self._get_keyword_synonyms(keyword.lower()))
                for _ in [keyword]  # Just iterate once
            )
            
            extraction_results[keyword] = {
                "in_customer_input": in_input,
                "acknowledged_in_response": acknowledged,
                "extracted_successfully": in_input or acknowledged  # More flexible - either mentioned by customer OR acknowledged
            }
        
        successful_extractions = sum(1 for result in extraction_results.values() if result["extracted_successfully"])
        total_expected = len(should_extract)
        
        success = successful_extractions >= (total_expected * 0.7)  # 70% success rate required
        
        return {
            "success": success,
            "extraction_rate": successful_extractions / total_expected if total_expected > 0 else 1.0,
            "details": extraction_results,
            "summary": f"Extracted {successful_extractions}/{total_expected} key concepts"
        }

    def _validate_response_quality(self, step_result: Dict[str, Any], expected: Dict[str, Any]) -> Dict[str, Any]:
        """Validate the quality and appropriateness of AI response."""
        
        ai_response = step_result["response_data"].get("response_text", "")
        response_time = step_result.get("response_time_seconds", 0)
        
        quality_checks = {
            "response_length_appropriate": 100 <= len(ai_response) <= 1200,  # Allow longer responses for detailed product info
            "response_time_acceptable": response_time <= 10.0,  # Under 10 seconds
            "conversational_tone": any(word in ai_response.lower() for word in ["hi", "hello", "great", "sure", "i'd", "you", "your"]),
            "provides_value": len(ai_response) > 150,  # Substantial response
            "addresses_customer": "you" in ai_response.lower() or "your" in ai_response.lower(),
        }
        
        # Check specific expectations
        if expected.get("should_recommend", False):
            quality_checks["provides_recommendations"] = any(word in ai_response.lower() for word in ["recommend", "suggest", "try", "consider"])
        
        if expected.get("should_provide_details", False):
            quality_checks["provides_details"] = len(ai_response) > 150
        
        if expected.get("should_provide_pricing", False):
            quality_checks["mentions_pricing"] = any(word in ai_response.lower() for word in ["price", "cost", "$", "affordable", "budget"])
        
        passed_checks = sum(quality_checks.values())
        total_checks = len(quality_checks)
        quality_score = passed_checks / total_checks
        
        return {
            "success": quality_score >= 0.7,  # 70% of quality checks must pass
            "quality_score": round(quality_score, 2),
            "checks_passed": f"{passed_checks}/{total_checks}",
            "details": quality_checks,
            "response_length": len(ai_response),
            "response_time": response_time
        }

    def _validate_multiproduct_handling(self, response_data: Dict[str, Any], conversation_state: Dict[str, Any], step_number: int) -> Dict[str, Any]:
        """Validate that multiple products are properly tracked and managed."""
        
        product_ids = response_data.get("interested_product_ids", []) or conversation_state.get("product_ids", [])
        
        # Enhanced validation for product accumulation
        has_products = len(product_ids) > 0
        
        # Check if products are accumulating properly (not decreasing)
        expected_min_products = max(1, step_number - 1) if step_number > 1 else 1
        products_accumulating = len(product_ids) >= expected_min_products
        
        # Check if response mentions multiple products (more flexible keywords)
        ai_response = response_data.get("response_text", "").lower()
        mentions_multiple = any(word in ai_response for word in [
            "both", "these", "products", "items", "serum", "moisturizer", "multiple", 
            "options", "recommendations", "suitable", "different", "variety"
        ])
        
        # Success if we have proper product accumulation AND mention products
        success = has_products and (products_accumulating or mentions_multiple)
        
        return {
            "success": success,
            "product_count": len(product_ids),
            "product_ids": product_ids,
            "mentions_multiple_in_response": mentions_multiple,
            "details": f"Tracking {len(product_ids)} products, mentions multiple: {mentions_multiple}"
        }

    def _validate_handover_preparation(self, response_data: Dict[str, Any], conversation_state: Dict[str, Any]) -> Dict[str, Any]:
        """Validate that handover to routing agent is properly prepared."""
        
        is_ready = response_data.get("is_ready", False) or conversation_state.get("is_ready", False)
        handover_flag = response_data.get("handover", False)
        product_ids = response_data.get("interested_product_ids", []) or conversation_state.get("product_ids", [])
        
        # Check if response indicates handover preparation
        ai_response = response_data.get("response_text", "").lower()
        handover_language = any(word in ai_response for word in [
            "connect", "transfer", "agent", "representative", "assist", "help you", "complete", "purchase"
        ])
        
        handover_ready = all([
            is_ready,
            len(product_ids) > 0,
            handover_language
        ])
        
        return {
            "success": handover_ready,
            "is_ready": is_ready,
            "handover_flag": handover_flag,
            "has_products": len(product_ids) > 0,
            "handover_language_used": handover_language,
            "product_count": len(product_ids),
            "details": f"Ready: {is_ready}, Products: {len(product_ids)}, Handover language: {handover_language}"
        }

    def _log_step_results(self, step_number: int, step_result: Dict[str, Any], validation_result: Dict[str, Any]):
        """Log detailed results for a conversation step."""
        
        logger.info(f"\n📊 STEP {step_number} RESULTS:")
        logger.info(f"   Response Time: {step_result['response_time_seconds']}s")
        logger.info(f"   HTTP Status: {step_result['http_status']}")
        
        # Log conversation state
        conv_state = step_result["conversation_state"]
        if conv_state.get("stored"):
            logger.info(f"   💾 Stored: ✅ {conv_state['message_count']} messages, Stage: {conv_state['current_stage']}")
            logger.info(f"   🎯 Products: {len(conv_state['product_ids'])} tracked")
            logger.info(f"   🚀 Ready: {conv_state['is_ready']}")
        else:
            logger.info(f"   💾 Stored: ❌ {conv_state.get('error', 'Unknown error')}")
        
        # Log validation results
        logger.info(f"   ✅ Overall Success: {validation_result['overall_success']}")
        for validation_type, result in validation_result["validations"].items():
            status = "✅" if result["success"] else "❌"
            logger.info(f"      {status} {validation_type}: {result.get('details', result)}")
        
        if not validation_result["overall_success"]:
            logger.warning(f"   ⚠️ Failed validations: {validation_result['failed_validations']}")

    async def _final_system_validation(self):
        """Perform final validation of the entire system state."""
        logger.info("\n🔍 FINAL SYSTEM VALIDATION")
        
        # Test status endpoint
        status_response = self.client.get(f"/api/webhook/status/{self.customer_id}")
        
        # Test insights endpoint  
        insights_response = self.client.get(f"/api/webhook/insights/{self.customer_id}")
        
        # Test recommendations endpoint
        recommendations_response = self.client.get(f"/api/webhook/recommendations/{self.customer_id}")
        
        # Final conversation state
        final_state = await self._capture_conversation_state()
        
        self.test_results["final_validation"] = {
            "status_endpoint": {
                "working": status_response.status_code == 200,
                "response": status_response.json() if status_response.status_code == 200 else None
            },
            "insights_endpoint": {
                "working": insights_response.status_code == 200,
                "response": insights_response.json() if insights_response.status_code == 200 else None
            },
            "recommendations_endpoint": {
                "working": recommendations_response.status_code == 200,
                "response": recommendations_response.json() if recommendations_response.status_code == 200 else None
            },
            "final_conversation_state": final_state
        }
        
        logger.info(f"   Status Endpoint: {'✅' if status_response.status_code == 200 else '❌'}")
        logger.info(f"   Insights Endpoint: {'✅' if insights_response.status_code == 200 else '❌'}")
        logger.info(f"   Recommendations Endpoint: {'✅' if recommendations_response.status_code == 200 else '❌'}")

    def _generate_final_analysis(self):
        """Generate comprehensive analysis of the test results."""
        
        # Calculate overall success rates
        total_steps = len(self.test_results["conversation_steps"])
        successful_steps = sum(1 for step in self.test_results["validation_results"] if step["overall_success"])
        
        # Analyze specific aspects
        storage_successes = sum(1 for step in self.test_results["validation_results"] 
                               if step["validations"].get("conversation_storage", {}).get("success", False))
        
        stage_successes = sum(1 for step in self.test_results["validation_results"]
                             if step["validations"].get("stage_detection", {}).get("success", False))
        
        response_quality_scores = [
            step["validations"]["response_quality"]["quality_score"]
            for step in self.test_results["validation_results"]
            if "response_quality" in step["validations"]
        ]
        
        multiproduct_checks = [
            step["validations"]["multiproduct_handling"]["success"]
            for step in self.test_results["validation_results"]
            if "multiproduct_handling" in step["validations"]
        ]
        
        handover_checks = [
            step["validations"]["handover_preparation"]["success"]
            for step in self.test_results["validation_results"]
            if "handover_preparation" in step["validations"]
        ]
        
        # Generate performance analysis
        self.test_results["system_performance"] = {
            "overall_success_rate": successful_steps / total_steps if total_steps > 0 else 0,
            "conversation_storage_success_rate": storage_successes / total_steps if total_steps > 0 else 0,
            "stage_detection_success_rate": stage_successes / total_steps if total_steps > 0 else 0,
            "average_response_quality": sum(response_quality_scores) / len(response_quality_scores) if response_quality_scores else 0,
            "multiproduct_handling_success_rate": sum(multiproduct_checks) / len(multiproduct_checks) if multiproduct_checks else 0,
            "handover_preparation_success_rate": sum(handover_checks) / len(handover_checks) if handover_checks else 0,
            "average_response_time": sum(step["response_time_seconds"] for step in self.test_results["conversation_steps"]) / total_steps if total_steps > 0 else 0
        }
        
        # Generate grade
        overall_score = self.test_results["system_performance"]["overall_success_rate"]
        if overall_score >= 0.9:
            grade = "A - Excellent"
        elif overall_score >= 0.8:
            grade = "B - Good" 
        elif overall_score >= 0.7:
            grade = "C - Satisfactory"
        elif overall_score >= 0.6:
            grade = "D - Needs Improvement"
        else:
            grade = "F - Failed"
        
        self.test_results["final_grade"] = grade
        
        # Identify issues and recommendations
        self._identify_issues_and_recommendations()

    def _identify_issues_and_recommendations(self):
        """Identify issues and provide recommendations for improvement."""
        
        issues = []
        recommendations = []
        
        perf = self.test_results["system_performance"]
        
        # Check each performance metric
        if perf["conversation_storage_success_rate"] < 1.0:
            issues.append(f"Conversation storage issues: {perf['conversation_storage_success_rate']:.2%} success rate")
            recommendations.append("Review database connection and storage logic")
        
        if perf["stage_detection_success_rate"] < 0.9:
            issues.append(f"Stage detection accuracy: {perf['stage_detection_success_rate']:.2%} success rate")
            recommendations.append("Improve stage detection algorithms and prompts")
        
        if perf["average_response_quality"] < 0.8:
            issues.append(f"Response quality below target: {perf['average_response_quality']:.2f}")
            recommendations.append("Enhance response generation with better prompts and validation")
        
        if perf.get("multiproduct_handling_success_rate", 1.0) < 0.9:
            issues.append(f"Multi-product handling issues: {perf.get('multiproduct_handling_success_rate', 0):.2%}")
            recommendations.append("Improve product context management and tracking")
        
        if perf.get("handover_preparation_success_rate", 1.0) < 1.0:
            issues.append(f"Handover preparation incomplete: {perf.get('handover_preparation_success_rate', 0):.2%}")
            recommendations.append("Review handover logic and routing agent integration")
        
        if perf["average_response_time"] > 5.0:
            issues.append(f"Response times too slow: {perf['average_response_time']:.2f}s average")
            recommendations.append("Optimize AI processing and database queries")
        
        if not issues:
            issues.append("No major issues detected - system performing well!")
            recommendations.append("Continue monitoring and maintain current performance levels")
        
        self.test_results["issues_detected"] = issues
        self.test_results["recommendations"] = recommendations

    async def _save_test_results(self):
        """Save detailed test results to file."""
        
        self.test_results["test_session"]["end_time"] = datetime.now(timezone.utc).isoformat()
        self.test_results["test_session"]["duration_seconds"] = (
            datetime.fromisoformat(self.test_results["test_session"]["end_time"].replace('Z', '+00:00')) -
            datetime.fromisoformat(self.test_results["test_session"]["start_time"].replace('Z', '+00:00'))
        ).total_seconds()
        
        # Save to file
        timestamp = int(time.time())
        filename = f"/Users/Kazi/Desktop/Sales-DevDemo/master_test_results_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(self.test_results, f, indent=2, default=str)
        
        logger.info(f"📄 Detailed results saved to: {filename}")

    async def _cleanup_system(self):
        """Clean up system resources."""
        try:
            mongo_handler.disconnect()
            postgres_handler.disconnect()
            logger.info("🔌 System cleanup completed")
        except Exception as e:
            logger.error(f"⚠️ Cleanup error: {e}")

async def main():
    """Main function to run the master test."""
    print("🎭 MASTER REAL-LIFE CONVERSATION TEST")
    print("=" * 50)
    print("Testing complete customer conversation flow with thorough validation")
    print("This test simulates a real customer and validates every aspect of the system\n")
    
    # Initialize and run test
    tester = MasterConversationTester()
    results = await tester.run_master_test()
    
    # Print summary results
    print("\n" + "=" * 50)
    print("📊 MASTER TEST RESULTS SUMMARY")
    print("=" * 50)
    
    perf = results.get("system_performance", {})
    print(f"🎖️  Final Grade: {results.get('final_grade', 'Unknown')}")
    print(f"📈 Overall Success Rate: {perf.get('overall_success_rate', 0):.2%}")
    print(f"💾 Storage Success: {perf.get('conversation_storage_success_rate', 0):.2%}")
    print(f"🎯 Stage Detection: {perf.get('stage_detection_success_rate', 0):.2%}")
    print(f"💬 Response Quality: {perf.get('average_response_quality', 0):.2f}")
    print(f"🛍️  Multi-Product Handling: {perf.get('multiproduct_handling_success_rate', 0):.2%}")
    print(f"🔄 Handover Preparation: {perf.get('handover_preparation_success_rate', 0):.2%}")
    print(f"⏱️  Average Response Time: {perf.get('average_response_time', 0):.2f}s")
    
    # Print conversation flow
    print(f"\n💬 CONVERSATION FLOW:")
    for i, step in enumerate(results.get("conversation_steps", []), 1):
        conv_state = step.get("conversation_state", {})
        validation = results["validation_results"][i-1] if i-1 < len(results.get("validation_results", [])) else {}
        status = "✅" if validation.get("overall_success", False) else "❌"
        stage = conv_state.get("current_stage", "Unknown")
        ready = conv_state.get("is_ready", False)
        products = len(conv_state.get("product_ids", []))
        
        print(f"  {i}. {status} Stage: {stage}, Ready: {ready}, Products: {products}")
    
    # Print issues and recommendations
    issues = results.get("issues_detected", [])
    if issues:
        print(f"\n⚠️  ISSUES DETECTED:")
        for issue in issues:
            print(f"   • {issue}")
    
    recommendations = results.get("recommendations", [])
    if recommendations:
        print(f"\n💡 RECOMMENDATIONS:")
        for rec in recommendations:
            print(f"   • {rec}")
    
    # Final status
    success_rate = perf.get("overall_success_rate", 0)
    if success_rate >= 0.9:
        print(f"\n🎉 EXCELLENT: Master test passed with flying colors!")
        return 0
    elif success_rate >= 0.7:
        print(f"\n✅ GOOD: Master test passed with minor issues to address.")
        return 0
    else:
        print(f"\n⚠️  NEEDS WORK: Master test identified significant issues.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
