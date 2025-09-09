#!/usr/bin/env python3
"""
Real-Life Conversation Simulation Master Test
=============================================

Comprehensive simulation of a real customer conversation scenario.
Tests the complete conversation system from initial contact to routing agent handover.

This test simulates:
1. Realistic customer conversation flow
2. Database storage verification at each step
3. Information extraction and context management
4. Multi-product interest handling
5. State transition validation
6. Response quality assessment
7. Routing agent handover verification
"""

import asyncio
import json
import logging
import sys
import time
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
import httpx
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
from app.db.mongo_handler import mongo_handler
from app.db.postgres_handler import postgres_handler

class RealLifeConversationSimulator:
    """
    Simulates a complete real-life customer conversation.
    Tests every aspect of the conversation system thoroughly.
    """

    def __init__(self):
        self.client = TestClient(app)
        self.customer_id = f"real_customer_{int(time.time())}"
        self.conversation_log = []
        self.database_states = []
        self.logger = logging.getLogger(__name__)

        # Realistic conversation scenario
        self.conversation_scenario = [
            {
                "step": "initial_greeting",
                "customer_message": "Hi there! I'm looking for some good skincare products for my dry skin.",
                "expected_stage": "INITIAL_INTEREST",
                "expected_intent": "inquire",
                "description": "Customer initiates contact with general skincare interest"
            },
            {
                "step": "product_inquiry",
                "customer_message": "I need something for anti-aging and also maybe a vitamin C serum. What would you recommend?",
                "expected_stage": "PRODUCT_DISCOVERY",
                "expected_intent": "inquire",
                "description": "Customer shows interest in specific products"
            },
            {
                "step": "price_check",
                "customer_message": "How much do these products cost? I'm on a budget but willing to invest in quality.",
                "expected_stage": "PRICE_EVALUATION",
                "expected_intent": "inquire",
                "description": "Customer evaluates pricing and shows budget consideration"
            },
            {
                "step": "purchase_consideration",
                "customer_message": "The Vitamin C Serum sounds really good. I'm also interested in that Anti-Aging Cream you mentioned.",
                "expected_stage": "PURCHASE_INTENT",
                "expected_intent": "buy",
                "description": "Customer shows purchase intent for multiple products"
            },
            {
                "step": "final_confirmation",
                "customer_message": "Yes, I want to buy both the Vitamin C Serum and the Anti-Aging Cream. Please help me complete the purchase.",
                "expected_stage": "PURCHASE_CONFIRMATION",
                "expected_intent": "buy",
                "description": "Customer confirms purchase for multiple products"
            }
        ]

    async def run_real_life_simulation(self) -> Dict[str, Any]:
        """
        Run the complete real-life conversation simulation.

        Returns:
            Dict containing comprehensive test results and analysis
        """
        self.logger.info("🎭 Starting Real-Life Conversation Simulation")
        self.logger.info("=" * 60)

        simulation_results = {
            "simulation_timestamp": datetime.now(timezone.utc).isoformat(),
            "customer_id": self.customer_id,
            "scenario": "real_life_customer_journey",
            "conversation_steps": [],
            "database_verification": [],
            "state_transitions": [],
            "response_quality_analysis": [],
            "multi_product_handling": [],
            "final_handover": None,
            "overall_assessment": {},
            "issues_found": []
        }

        try:
            # Step 0: Connect to databases
            self.logger.info("\n🔌 Connecting to databases...")
            try:
                mongo_handler.connect()
                self.logger.info("✅ MongoDB connection established")
            except Exception as e:
                self.logger.error(f"❌ MongoDB connection failed: {e}")
                raise

            try:
                postgres_handler.connect()
                self.logger.info("✅ PostgreSQL connection established")
            except Exception as e:
                self.logger.error(f"❌ PostgreSQL connection failed: {e}")
                raise

            # Step 1: Pre-simulation database check
            self.logger.info("\n📋 Pre-Simulation: Database State Check")
            initial_db_state = await self.check_database_state("pre_simulation")
            simulation_results["database_verification"].append(initial_db_state)

            # Step 2: Execute conversation scenario
            for i, conversation_step in enumerate(self.conversation_scenario, 1):
                self.logger.info(f"\n🎯 Step {i}: {conversation_step['step'].upper()}")
                self.logger.info(f"   {conversation_step['description']}")

                step_result = await self.execute_conversation_step(conversation_step, i)
                simulation_results["conversation_steps"].append(step_result)

                # Verify database storage after each step
                db_verification = await self.verify_database_storage(i, conversation_step)
                simulation_results["database_verification"].append(db_verification)

                # Analyze state transitions
                if i > 1:
                    state_analysis = self.analyze_state_transition(
                        simulation_results["conversation_steps"][-2],
                        simulation_results["conversation_steps"][-1]
                    )
                    simulation_results["state_transitions"].append(state_analysis)

                # Check multi-product context
                if i >= 2:  # After product inquiry
                    multi_product_check = await self.check_multi_product_context(i)
                    simulation_results["multi_product_handling"].append(multi_product_check)

            # Step 3: Post-simulation analysis
            self.logger.info("\n📋 Post-Simulation: Final Analysis")

            # Check final handover
            handover_result = await self.verify_routing_handover()
            simulation_results["final_handover"] = handover_result

            # Overall assessment
            simulation_results["overall_assessment"] = self.generate_overall_assessment(simulation_results)

            # Generate issues summary
            simulation_results["issues_found"] = self.identify_issues(simulation_results)

            self.logger.info(f"\n🎭 Simulation Complete: {simulation_results['overall_assessment']['grade']}")

        except Exception as e:
            self.logger.error(f"❌ Simulation failed: {e}")
            simulation_results["simulation_status"] = "failed"
            simulation_results["error"] = str(e)

        finally:
            # Disconnect from databases
            try:
                mongo_handler.disconnect()
                postgres_handler.disconnect()
                self.logger.info("🔌 Database connections closed")
            except Exception as e:
                self.logger.error(f"Error disconnecting databases: {e}")

        return simulation_results

    async def execute_conversation_step(self, step_config: Dict[str, Any], step_number: int) -> Dict[str, Any]:
        """Execute a single conversation step and analyze the response."""
        try:
            # Send customer message
            message_data = {
                "sender": self.customer_id,
                "recipient": "page_123",
                "text": step_config["customer_message"]
            }

            start_time = time.time()
            response = self.client.post("/api/webhook", json=message_data)
            response_time = time.time() - start_time

            response_data = response.json()

            # Analyze response quality
            response_analysis = self.analyze_response_quality(
                step_config, response_data, response_time
            )

            # Extract conversation context
            conversation_context = {
                "step_number": step_number,
                "step_name": step_config["step"],
                "customer_message": step_config["customer_message"],
                "ai_response": response_data.get("response_text", ""),
                "response_time_seconds": round(response_time, 2),
                "http_status": response.status_code,
                "conversation_stage": response_data.get("conversation_stage"),
                "is_ready": response_data.get("is_ready"),
                "handover": response_data.get("handover", False),
                "product_ids": response_data.get("interested_product_ids", []),
                "confidence": response_data.get("confidence", 0),
                "expected_stage": step_config["expected_stage"],
                "stage_match": response_data.get("conversation_stage") == step_config["expected_stage"],
                "response_analysis": response_analysis,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

            self.conversation_log.append(conversation_context)

            return conversation_context

        except Exception as e:
            return {
                "step_number": step_number,
                "step_name": step_config["step"],
                "error": str(e),
                "status": "failed"
            }

    async def check_database_state(self, context: str) -> Dict[str, Any]:
        """Check the current state of the database."""
        try:
            # Check MongoDB conversation state
            mongo_state = self.check_mongodb_state()

            # Check PostgreSQL product data
            postgres_state = await self.check_postgresql_state()

            return {
                "context": context,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "mongodb": mongo_state,
                "postgresql": postgres_state,
                "status": "success"
            }

        except Exception as e:
            return {
                "context": context,
                "error": str(e),
                "status": "failed"
            }

    def check_mongodb_state(self) -> Dict[str, Any]:
        """Check MongoDB conversation storage."""
        try:
            # Get conversation collection
            db = mongo_handler.get_database()
            conversations_collection = db["conversations"]

            # Count total conversations
            total_conversations = conversations_collection.count_documents({})

            # Check for our test customer
            customer_conversation = conversations_collection.find_one(
                {"sender_id": self.customer_id}
            )

            return {
                "total_conversations": total_conversations,
                "customer_conversation_exists": customer_conversation is not None,
                "customer_conversation_data": customer_conversation,
                "status": "success"
            }

        except Exception as e:
            return {
                "error": str(e),
                "status": "failed"
            }

    async def check_postgresql_state(self) -> Dict[str, Any]:
        """Check PostgreSQL product data."""
        try:
            # Get product count
            product_count_query = "SELECT COUNT(*) FROM products"
            product_count_result = postgres_handler.execute_query(product_count_query)

            # Get sample products
            sample_products_query = """
            SELECT id, name, category_id, price
            FROM products
            LIMIT 5
            """
            sample_products = postgres_handler.execute_query(sample_products_query)

            return {
                "total_products": product_count_result[0][0] if product_count_result else 0,
                "sample_products": [
                    {
                        "id": str(row[0]),
                        "name": row[1],
                        "category": row[2],
                        "price": float(row[3]) if row[3] else 0
                    }
                    for row in sample_products
                ] if sample_products else [],
                "status": "success"
            }

        except Exception as e:
            return {
                "error": str(e),
                "status": "failed"
            }

    async def verify_database_storage(self, step_number: int, step_config: Dict[str, Any]) -> Dict[str, Any]:
        """Verify that conversation data is properly stored in database."""
        try:
            # Check MongoDB for conversation storage
            db = mongo_handler.get_database()
            conversations_collection = db["conversations"]

            # Find conversation for our customer
            conversation_doc = conversations_collection.find_one(
                {"sender_id": self.customer_id}
            )

            if conversation_doc:
                # Analyze stored conversation data
                # Handle nested conversation structure
                conversation_data = conversation_doc.get("conversation", {})
                if isinstance(conversation_data, dict):
                    stored_messages = conversation_data.get("conversation", [])
                else:
                    stored_messages = conversation_data if isinstance(conversation_data, list) else []

                current_stage = conversation_doc.get("current_stage", "UNKNOWN")
                product_ids = conversation_doc.get("product_ids", [])

                verification = {
                    "step_number": step_number,
                    "conversation_stored": True,
                    "messages_count": len(stored_messages),
                    "current_stage": current_stage,
                    "stored_product_ids": product_ids,
                    "last_message_matches": False,
                    "stage_consistency": current_stage == self.conversation_log[-1]["conversation_stage"] if self.conversation_log else False
                }

                # Check if last customer message matches what we sent
                # We need to find the last customer message, not just the last message
                if stored_messages and self.conversation_log:
                    last_sent = self.conversation_log[-1]["customer_message"]
                    
                    # Find the last customer message in stored messages
                    customer_messages = [msg for msg in stored_messages if msg.get("role") == "user" or msg.get("sender") == "user"]
                    
                    if customer_messages:
                        last_stored_customer = customer_messages[-1]
                        # Check both content and text fields for message content
                        stored_content = last_stored_customer.get("content") or last_stored_customer.get("text", "")
                        verification["last_message_matches"] = stored_content.strip() == last_sent.strip()
                    else:
                        # If no customer messages found, check if any message contains our sent text
                        verification["last_message_matches"] = any(
                            last_sent.strip() in (msg.get("content", "") + msg.get("text", "")).strip()
                            for msg in stored_messages
                        )

                return verification
            else:
                return {
                    "step_number": step_number,
                    "conversation_stored": False,
                    "error": "No conversation document found for customer"
                }

        except Exception as e:
            return {
                "step_number": step_number,
                "error": str(e),
                "status": "failed"
            }

    def analyze_state_transition(self, previous_step: Dict[str, Any], current_step: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the transition between conversation states."""
        try:
            prev_stage = previous_step.get("conversation_stage")
            curr_stage = current_step.get("conversation_stage")

            # Define expected transitions
            expected_transitions = {
                "INITIAL_INTEREST": ["PRODUCT_DISCOVERY", "PRICE_EVALUATION"],
                "PRODUCT_DISCOVERY": ["PRICE_EVALUATION", "PURCHASE_INTENT"],
                "PRICE_EVALUATION": ["PURCHASE_INTENT", "PURCHASE_CONFIRMATION"],
                "PURCHASE_INTENT": ["PURCHASE_CONFIRMATION"],
                "PURCHASE_CONFIRMATION": ["PURCHASE_CONFIRMATION"]
            }

            valid_transition = curr_stage in expected_transitions.get(prev_stage, [])

            return {
                "from_stage": prev_stage,
                "to_stage": curr_stage,
                "transition_valid": valid_transition,
                "expected_transitions": expected_transitions.get(prev_stage, []),
                "stage_progression": self.calculate_stage_progression(prev_stage, curr_stage),
                "analysis": "Good transition" if valid_transition else "Unexpected transition"
            }

        except Exception as e:
            return {
                "error": str(e),
                "status": "failed"
            }

    def calculate_stage_progression(self, from_stage: str, to_stage: str) -> str:
        """Calculate if the conversation is progressing toward purchase."""
        stage_order = ["INITIAL_INTEREST", "PRODUCT_DISCOVERY", "PRICE_EVALUATION", "PURCHASE_INTENT", "PURCHASE_CONFIRMATION"]

        try:
            from_index = stage_order.index(from_stage)
            to_index = stage_order.index(to_stage)

            if to_index > from_index:
                return "progressing"
            elif to_index == from_index:
                return "maintaining"
            else:
                return "regressing"
        except ValueError:
            return "unknown"

    async def check_multi_product_context(self, step_number: int) -> Dict[str, Any]:
        """Check if the system properly handles multiple products in context."""
        try:
            # Get current conversation state
            db = mongo_handler.get_database()
            conversations_collection = db["conversations"]

            conversation_doc = conversations_collection.find_one(
                {"sender_id": self.customer_id}
            )

            if conversation_doc:
                # Handle nested conversation structure
                conversation_data = conversation_doc.get("conversation", {})
                if isinstance(conversation_data, dict):
                    product_ids = conversation_data.get("product_ids", [])
                    interested_products = conversation_data.get("interested_products", [])
                else:
                    product_ids = conversation_doc.get("product_ids", [])
                    interested_products = conversation_doc.get("interested_products", [])

                # Check if we have multiple products
                multi_product_context = {
                    "step_number": step_number,
                    "product_ids_count": len(product_ids),
                    "interested_products_count": len(interested_products),
                    "has_multiple_products": len(product_ids) > 1,
                    "product_ids": product_ids,
                    "interested_products": interested_products,
                    "context_maintained": len(product_ids) > 0
                }

                # Check if products are properly stored
                if step_number >= 4:  # After purchase consideration step
                    multi_product_context["expected_multiple_products"] = True
                    multi_product_context["multiple_products_handled"] = len(product_ids) >= 2

                return multi_product_context
            else:
                return {
                    "step_number": step_number,
                    "error": "No conversation document found",
                    "status": "failed"
                }

        except Exception as e:
            return {
                "step_number": step_number,
                "error": str(e),
                "status": "failed"
            }

    def analyze_response_quality(self, step_config: Dict[str, Any], response_data: Dict[str, Any], response_time: float) -> Dict[str, Any]:
        """Analyze the quality of AI responses."""
        try:
            response_text = response_data.get("response_text", "").lower()
            customer_message = step_config["customer_message"].lower()

            # Quality checks
            quality_analysis = {
                "response_length": len(response_text),
                "response_time_seconds": response_time,
                "is_responsive": len(response_text) > 10,
                "is_conversational": any(word in response_text for word in ["hi", "hello", "great", "sure", "certainly", "absolutely"]),
                "addresses_customer": any(word in response_text for word in ["you", "your", "skin", "product", "recommend"]),
                "shows_enthusiasm": any(word in response_text for word in ["great", "excellent", "wonderful", "amazing", "love"]),
                "provides_value": any(word in response_text for word in ["recommend", "suggest", "help", "benefit", "price"]),
                "calls_to_action": any(word in response_text for word in ["let me know", "tell me", "would you like", "interested"]),
                "stage_appropriate": self.check_stage_appropriateness(step_config, response_data)
            }

            # Overall quality score
            quality_score = sum(quality_analysis.values()) / len(quality_analysis)
            quality_analysis["overall_quality_score"] = round(quality_score, 2)
            quality_analysis["quality_rating"] = self.get_quality_rating(quality_score)

            return quality_analysis

        except Exception as e:
            return {
                "error": str(e),
                "status": "failed"
            }

    def check_stage_appropriateness(self, step_config: Dict[str, Any], response_data: Dict[str, Any]) -> bool:
        """Check if response is appropriate for the conversation stage."""
        stage = response_data.get("conversation_stage", "")
        response_text = response_data.get("response_text", "").lower()

        stage_checks = {
            "INITIAL_INTEREST": ["recommend", "help", "tell me", "interested"],
            "PRODUCT_DISCOVERY": ["recommend", "suggest", "benefit", "price"],
            "PRICE_EVALUATION": ["price", "cost", "budget", "discount", "value"],
            "PURCHASE_INTENT": ["great", "excellent", "confirm", "ready", "purchase"],
            "PURCHASE_CONFIRMATION": ["transfer", "handover", "agent", "complete", "purchase"]
        }

        expected_keywords = stage_checks.get(stage, [])
        return any(keyword in response_text for keyword in expected_keywords)

    def get_quality_rating(self, score: float) -> str:
        """Convert quality score to rating."""
        if score >= 0.8:
            return "excellent"
        elif score >= 0.6:
            return "good"
        elif score >= 0.4:
            return "fair"
        else:
            return "needs_improvement"

    async def verify_routing_handover(self) -> Dict[str, Any]:
        """Verify the routing agent handover process."""
        try:
            # Get final conversation status
            status_response = self.client.get(f"/api/webhook/status/{self.customer_id}")
            status_data = status_response.json()

            # Get conversation insights
            insights_response = self.client.get(f"/api/webhook/insights/{self.customer_id}")
            insights_data = insights_response.json()

            # Get product recommendations
            recommendations_response = self.client.get(f"/api/webhook/recommendations/{self.customer_id}")
            recommendations_data = recommendations_response.json()

            # Analyze handover readiness
            final_step = self.conversation_log[-1] if self.conversation_log else {}
            is_ready = final_step.get("is_ready", False)
            handover = final_step.get("handover", False)
            product_ids = final_step.get("product_ids", [])

            handover_analysis = {
                "handover_timestamp": datetime.now(timezone.utc).isoformat(),
                "is_ready_for_handover": is_ready,
                "handover_flag": handover,
                "final_stage": final_step.get("conversation_stage"),
                "product_ids_count": len(product_ids),
                "product_ids": product_ids,
                "conversation_length": len(self.conversation_log),
                "status_endpoint_working": status_response.status_code == 200,
                "insights_endpoint_working": insights_response.status_code == 200,
                "recommendations_endpoint_working": recommendations_response.status_code == 200,
                "handover_data_complete": all([
                    is_ready,
                    handover,
                    len(product_ids) > 0,
                    final_step.get("conversation_stage") == "PURCHASE_CONFIRMATION"
                ])
            }

            return handover_analysis

        except Exception as e:
            return {
                "error": str(e),
                "status": "failed"
            }

    def generate_overall_assessment(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate overall assessment of the simulation."""
        try:
            conversation_steps = results.get("conversation_steps", [])
            successful_steps = len([s for s in conversation_steps if s.get("status") != "failed"])
            total_steps = len(conversation_steps)

            # Calculate success rate
            success_rate = successful_steps / total_steps if total_steps > 0 else 0

            # Check state transitions
            state_transitions = results.get("state_transitions", [])
            valid_transitions = len([t for t in state_transitions if t.get("transition_valid", False)])
            transition_success_rate = valid_transitions / len(state_transitions) if state_transitions else 0

            # Check database storage
            db_verifications = results.get("database_verification", [])
            # Filter out pre_simulation check and only count conversation steps
            conversation_verifications = [v for v in db_verifications if v.get("step_number") is not None]
            successful_storage = len([v for v in conversation_verifications if v.get("conversation_stored", False) and v.get("last_message_matches", False)])
            storage_success_rate = successful_storage / len(conversation_verifications) if conversation_verifications else 0

            # Check response quality
            quality_scores = []
            for step in conversation_steps:
                analysis = step.get("response_analysis", {})
                score = analysis.get("overall_quality_score", 0)
                if score > 0:
                    quality_scores.append(score)

            avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0

            # Check multi-product handling
            multi_product_checks = results.get("multi_product_handling", [])
            multi_product_success = len([c for c in multi_product_checks if c.get("has_multiple_products", False)])
            multi_product_rate = multi_product_success / len(multi_product_checks) if multi_product_checks else 0

            # Overall grade
            overall_score = (success_rate + transition_success_rate + storage_success_rate + avg_quality + multi_product_rate) / 5

            if overall_score >= 0.8:
                grade = "A - Excellent"
            elif overall_score >= 0.6:
                grade = "B - Good"
            elif overall_score >= 0.4:
                grade = "C - Fair"
            else:
                grade = "D - Needs Improvement"

            return {
                "grade": grade,
                "overall_score": round(overall_score, 2),
                "success_rate": round(success_rate, 2),
                "transition_success_rate": round(transition_success_rate, 2),
                "storage_success_rate": round(storage_success_rate, 2),
                "average_response_quality": round(avg_quality, 2),
                "multi_product_success_rate": round(multi_product_rate, 2),
                "total_steps": total_steps,
                "successful_steps": successful_steps
            }

        except Exception as e:
            return {
                "error": str(e),
                "grade": "F - Failed",
                "status": "assessment_failed"
            }

    def identify_issues(self, results: Dict[str, Any]) -> List[str]:
        """Identify specific issues found during simulation."""
        issues = []

        # Check conversation steps
        for step in results.get("conversation_steps", []):
            if step.get("status") == "failed":
                issues.append(f"Step {step.get('step_number', '?')} failed: {step.get('error', 'Unknown error')}")

            if not step.get("stage_match", False):
                issues.append(f"Step {step.get('step_number', '?')}: Stage mismatch - Expected {step.get('expected_stage', '?')}, Got {step.get('conversation_stage', '?')}")

        # Check state transitions
        for transition in results.get("state_transitions", []):
            if not transition.get("transition_valid", True):
                issues.append(f"Invalid transition: {transition.get('from_stage', '?')} → {transition.get('to_stage', '?')}")

        # Check database storage
        for db_check in results.get("database_verification", []):
            if not db_check.get("conversation_stored", True):
                issues.append(f"Database storage failed at step {db_check.get('step_number', '?')}: {db_check.get('error', 'Unknown error')}")

        # Check response quality
        for step in results.get("conversation_steps", []):
            analysis = step.get("response_analysis", {})
            if analysis.get("overall_quality_score", 1) < 0.4:
                issues.append(f"Poor response quality at step {step.get('step_number', '?')}: Score {analysis.get('overall_quality_score', 0)}")

        # Check handover
        handover = results.get("final_handover", {})
        if not handover.get("is_ready_for_handover", False):
            issues.append("Final handover failed: Customer not marked as ready")

        if handover.get("product_ids_count", 0) == 0:
            issues.append("No product IDs in handover data")

        return issues if issues else ["No major issues found - system performing well!"]

async def main():
    """Main simulation execution function."""
    print("🎭 Real-Life Conversation Simulation Master Test")
    print("=" * 60)

    # Initialize simulator
    simulator = RealLifeConversationSimulator()

    # Run complete simulation
    results = await simulator.run_real_life_simulation()

    # Print results summary
    print("\n📊 Simulation Results Summary")
    print("=" * 35)

    assessment = results.get("overall_assessment", {})
    print(f"Overall Grade: {assessment.get('grade', 'Unknown')}")
    print(f"Overall Score: {assessment.get('overall_score', 0)}")
    print(f"Success Rate: {assessment.get('success_rate', 0)}")
    print(f"Steps Completed: {assessment.get('successful_steps', 0)}/{assessment.get('total_steps', 0)}")

    print("\n🔍 Detailed Metrics:")
    print(f"  State Transition Success: {assessment.get('transition_success_rate', 0)}")
    print(f"  Database Storage Success: {assessment.get('storage_success_rate', 0)}")
    print(f"  Average Response Quality: {assessment.get('average_response_quality', 0)}")
    print(f"  Multi-Product Handling: {assessment.get('multi_product_success_rate', 0)}")

    # Print conversation flow
    print("\n💬 Conversation Flow:")
    for i, step in enumerate(results.get("conversation_steps", []), 1):
        status_icon = "✅" if step.get("status") != "failed" else "❌"
        stage = step.get("conversation_stage", "Unknown")
        ready = step.get("is_ready", False)
        handover_flag = step.get("handover", False)
        print(f"  {i}. {status_icon} {step.get('step_name', 'Unknown')} → Stage: {stage}, Ready: {ready}, Handover: {handover_flag}")

    # Print handover status
    handover = results.get("final_handover", {})
    if handover:
        print("\n🔄 Routing Agent Handover:")
        print(f"  Ready for Handover: {handover.get('is_ready_for_handover', False)}")
        print(f"  Handover Flag: {handover.get('handover_flag', False)}")
        print(f"  Product IDs: {handover.get('product_ids', [])}")
        print(f"  Final Stage: {handover.get('final_stage', 'Unknown')}")
        print(f"  Handover Complete: {handover.get('handover_data_complete', False)}")

    # Print issues found
    issues = results.get("issues_found", [])
    if issues:
        print("\n⚠️  Issues Found:")
        for issue in issues:
            print(f"  • {issue}")

    # Save detailed results
    results_file = f"/Users/Kazi/Desktop/Sales-DevDemo/real_life_simulation_{int(time.time())}.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\n💾 Detailed results saved to: {results_file}")

    # Return exit code based on results
    if assessment.get("overall_score", 0) >= 0.6:
        print("\n🎉 SUCCESS: Real-life simulation passed!")
        return 0
    else:
        print("\n⚠️  WARNING: Some aspects need attention.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
