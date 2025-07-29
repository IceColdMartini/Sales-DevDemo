#!/usr/bin/env python3
"""
Comprehensive Conversation and Handover Test

This test covers the complete conversation flow as requested:
1. Random customer inquiries and LLM response quality
2. Product navigation and database product matching
3. Conversation continuity towards purchase
4. Clear purchase confirmation prompts with product details and prices
5. Proper is_ready flag management (false until explicit confirmation)
6. Multiple product handling
7. Product removal/modification scenarios
8. Analysis of current system vs potential LangChain improvements
"""

import requests
import json
import time
import sys
from typing import Dict, List, Any
from datetime import datetime

# Configuration
API_BASE_URL = "http://localhost:8000"
WEBHOOK_URL = f"{API_BASE_URL}/api/webhook"
HEALTH_URL = f"{API_BASE_URL}/health"

class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class ConversationHandoverTester:
    def __init__(self):
        self.test_results = []
        self.conversation_logs = []
        
    def log_result(self, test_name: str, passed: bool, details: str = ""):
        """Log test results for final summary"""
        result = {
            "test_name": test_name,
            "passed": passed,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = f"{Colors.OKGREEN}✅ PASS{Colors.ENDC}" if passed else f"{Colors.FAIL}❌ FAIL{Colors.ENDC}"
        print(f"{status} {test_name}: {details}")

    def log_conversation(self, sender_id: str, message: str, response: Dict):
        """Log conversation for analysis"""
        log_entry = {
            "sender_id": sender_id,
            "user_message": message,
            "agent_response": response.get('response_text', ''),
            "product_interested": response.get('product_interested'),
            "interested_product_ids": response.get('interested_product_ids', []),
            "is_ready": response.get('is_ready', False),
            "timestamp": datetime.now().isoformat()
        }
        self.conversation_logs.append(log_entry)

    def send_message(self, sender_id: str, message: str) -> Dict:
        """Send message to sales agent and return response"""
        payload = {
            "sender": sender_id,
            "recipient": "page_test",
            "text": message
        }
        
        try:
            response = requests.post(WEBHOOK_URL, json=payload, timeout=30)
            if response.status_code == 200:
                result = response.json()
                self.log_conversation(sender_id, message, result)
                return result
            else:
                print(f"{Colors.FAIL}API Error: {response.status_code} - {response.text}{Colors.ENDC}")
                return {}
        except Exception as e:
            print(f"{Colors.FAIL}Request Error: {e}{Colors.ENDC}")
            return {}

    def clear_conversation(self, sender_id: str):
        """Clear conversation history"""
        try:
            requests.delete(f"{API_BASE_URL}/api/webhook/conversation/{sender_id}")
            time.sleep(1)  # Allow cleanup
        except:
            pass  # Endpoint might not exist, that's OK

    def print_section(self, title: str):
        """Print section header"""
        print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 80}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}{title.center(80)}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 80}{Colors.ENDC}\n")

    def print_step(self, step_num: int, description: str):
        """Print test step"""
        print(f"\n{Colors.OKCYAN}📍 STEP {step_num}: {description}{Colors.ENDC}")
        print("-" * 60)

    def analyze_response_quality(self, user_message: str, agent_response: str, test_name: str):
        """Analyze if the agent response properly addresses the user and redirects to products"""
        response_lower = agent_response.lower()
        
        # Check if response acknowledges the user's message
        acknowledges_user = any(phrase in response_lower for phrase in [
            'understand', 'help', 'assist', 'great', 'perfect', 'excellent',
            'i see', 'absolutely', 'definitely', 'of course'
        ])
        
        # Check if response redirects to beauty/personal care products
        redirects_to_products = any(phrase in response_lower for phrase in [
            'beauty', 'skincare', 'hair care', 'perfume', 'shampoo', 'soap',
            'product', 'recommend', 'suggest', 'offer', 'collection'
        ])
        
        # Check if response is human-like and not robotic
        is_natural = len(agent_response) > 50 and any(phrase in response_lower for phrase in [
            'i\'d be happy', 'i can help', 'let me', 'would you', 'what kind',
            'specifically', 'perfect for', 'great choice'
        ])
        
        quality_score = sum([acknowledges_user, redirects_to_products, is_natural])
        passed = quality_score >= 2  # At least 2 out of 3 criteria
        
        details = f"Quality: {quality_score}/3 (Acknowledges: {acknowledges_user}, Redirects: {redirects_to_products}, Natural: {is_natural})"
        self.log_result(test_name, passed, details)
        
        return passed

    def test_1_random_customer_inquiries(self):
        """Test 1: Random customer inquiries and LLM response quality"""
        self.print_section("TEST 1: RANDOM CUSTOMER INQUIRIES & LLM RESPONSE QUALITY")
        
        test_scenarios = [
            {
                "message": "Hi there! I'm looking for something to make my hair smell amazing",
                "description": "Hair fragrance inquiry"
            },
            {
                "message": "My skin is really dry lately, especially in winter",
                "description": "Skincare problem statement"
            },
            {
                "message": "What's the weather like today?",
                "description": "Off-topic conversation"
            },
            {
                "message": "I need a gift for my girlfriend's birthday",
                "description": "Gift inquiry"
            },
            {
                "message": "Do you have anything for men's grooming?",
                "description": "Gender-specific product inquiry"
            }
        ]
        
        for i, scenario in enumerate(test_scenarios, 1):
            sender_id = f"test_1_scenario_{i}"
            self.clear_conversation(sender_id)
            
            self.print_step(i, scenario['description'])
            print(f"👤 Customer: {scenario['message']}")
            
            response = self.send_message(sender_id, scenario['message'])
            
            if response:
                agent_response = response.get('response_text', '')
                print(f"🤖 Agent: {agent_response[:200]}{'...' if len(agent_response) > 200 else ''}")
                print(f"🛍️  Product Interest: {response.get('product_interested', 'None')}")
                print(f"🚀 Ready Status: {response.get('is_ready', False)}")
                
                # Analyze response quality
                self.analyze_response_quality(
                    scenario['message'], 
                    agent_response, 
                    f"Response Quality - {scenario['description']}"
                )
                
                # Should not be ready after first message
                is_ready_correct = not response.get('is_ready', False)
                self.log_result(
                    f"Initial is_ready Status - {scenario['description']}", 
                    is_ready_correct,
                    f"is_ready={response.get('is_ready', False)} (should be False)"
                )
                
            time.sleep(2)

    def test_2_product_navigation_and_matching(self):
        """Test 2: Product navigation and database matching"""
        self.print_section("TEST 2: PRODUCT NAVIGATION & DATABASE MATCHING")
        
        sender_id = "test_2_product_navigation"
        self.clear_conversation(sender_id)
        
        # Step 1: General inquiry
        self.print_step(1, "General product inquiry")
        message1 = "I'm looking for a good perfume"
        print(f"👤 Customer: {message1}")
        response1 = self.send_message(sender_id, message1)
        
        if response1:
            print(f"🤖 Agent: {response1.get('response_text', '')[:150]}...")
            
            # Check if system understood the perfume inquiry
            has_product_interest = response1.get('product_interested') is not None
            self.log_result(
                "General Perfume Inquiry Detection", 
                has_product_interest,
                f"Detected: {response1.get('product_interested', 'None')}"
            )
        
        time.sleep(2)
        
        # Step 2: Specific product inquiry
        self.print_step(2, "Specific product inquiry")
        message2 = "Tell me about Wild Stone perfume"
        print(f"👤 Customer: {message2}")
        response2 = self.send_message(sender_id, message2)
        
        if response2:
            print(f"🤖 Agent: {response2.get('response_text', '')[:150]}...")
            print(f"🛍️  Product Interest: {response2.get('product_interested', 'None')}")
            print(f"🆔 Product IDs: {response2.get('interested_product_ids', [])}")
            
            # Check specific product matching
            product_name = response2.get('product_interested', '')
            product_ids = response2.get('interested_product_ids', [])
            
            wild_stone_detected = 'wild stone' in product_name.lower() if product_name else False
            has_product_ids = len(product_ids) > 0
            
            self.log_result(
                "Specific Product Detection (Wild Stone)",
                wild_stone_detected,
                f"Detected product: {product_name}"
            )
            
            self.log_result(
                "Product ID Extraction",
                has_product_ids,
                f"Product IDs: {product_ids}"
            )
        
        time.sleep(2)
        
        # Step 3: Multiple product inquiry  
        self.print_step(3, "Multiple product inquiry")
        message3 = "I also need a face wash, something with neem"
        print(f"👤 Customer: {message3}")
        response3 = self.send_message(sender_id, message3)
        
        if response3:
            print(f"🤖 Agent: {response3.get('response_text', '')[:150]}...")
            print(f"🛍️  Product Interest: {response3.get('product_interested', 'None')}")
            print(f"🆔 Product IDs: {response3.get('interested_product_ids', [])}")
            
            # Check if system tracks multiple products
            product_interest = response3.get('product_interested', '')
            product_ids = response3.get('interested_product_ids', [])
            
            tracks_multiple = ('perfume' in product_interest.lower() and 'face wash' in product_interest.lower()) or \
                             ('wild stone' in product_interest.lower() and 'neem' in product_interest.lower()) or \
                             len(product_ids) >= 2
            
            self.log_result(
                "Multiple Product Tracking",
                tracks_multiple,
                f"Products: {product_interest}, IDs: {len(product_ids)}"
            )

    def test_3_conversation_continuity(self):
        """Test 3: Conversation continuity towards purchase"""
        self.print_section("TEST 3: CONVERSATION CONTINUITY TOWARDS PURCHASE")
        
        sender_id = "test_3_continuity"
        self.clear_conversation(sender_id)
        
        conversation_flow = [
            {"message": "I need a good perfume for everyday use", "expected_ready": False},
            {"message": "Something that lasts long and smells fresh", "expected_ready": False},
            {"message": "Wild Stone sounds good, tell me more about it", "expected_ready": False},
            {"message": "What's the price?", "expected_ready": False},
            {"message": "That seems reasonable, I'm interested", "expected_ready": False}
        ]
        
        continuity_maintained = True
        
        for i, step in enumerate(conversation_flow, 1):
            self.print_step(i, f"Conversation step - {step['message'][:30]}...")
            print(f"👤 Customer: {step['message']}")
            
            response = self.send_message(sender_id, step['message'])
            
            if response:
                agent_response = response.get('response_text', '')
                is_ready = response.get('is_ready', False)
                product_interest = response.get('product_interested', '')
                
                print(f"🤖 Agent: {agent_response[:120]}...")
                print(f"🛍️  Product: {product_interest}")
                print(f"🚀 Ready: {is_ready} (Expected: {step['expected_ready']})")
                
                # Check if conversation maintains context from previous messages
                if i > 1:
                    maintains_context = any(word in agent_response.lower() for word in [
                        'perfume', 'wild stone', 'fragrance', 'scent'
                    ])
                    if not maintains_context:
                        continuity_maintained = False
                
                # Check is_ready expectation
                ready_correct = is_ready == step['expected_ready']
                if not ready_correct:
                    continuity_maintained = False
                    
                self.log_result(
                    f"Step {i} - Ready Status",
                    ready_correct,
                    f"is_ready={is_ready}, expected={step['expected_ready']}"
                )
            else:
                continuity_maintained = False
                
            time.sleep(2)
        
        self.log_result(
            "Overall Conversation Continuity",
            continuity_maintained,
            "Maintains context and proper is_ready progression"
        )

    def test_4_purchase_confirmation_prompts(self):
        """Test 4: Clear purchase confirmation prompts with product details and prices"""
        self.print_section("TEST 4: PURCHASE CONFIRMATION PROMPTS WITH DETAILS")
        
        sender_id = "test_4_confirmation"
        self.clear_conversation(sender_id)
        
        # Build up to purchase decision
        setup_messages = [
            "I need a perfume and face wash",
            "Tell me about Wild Stone perfume and Himalaya neem face wash",
            "How much do they cost?",
            "I think I want to buy them"
        ]
        
        for i, message in enumerate(setup_messages, 1):
            print(f"👤 Setup {i}: {message}")
            response = self.send_message(sender_id, message)
            if response:
                print(f"🤖 Agent: {response.get('response_text', '')[:100]}...")
            time.sleep(1.5)
        
        # Now test the critical confirmation prompt
        self.print_step(1, "Purchase confirmation prompt analysis")
        confirmation_message = "Yes, I want to buy both products"
        print(f"👤 Customer: {confirmation_message}")
        
        response = self.send_message(sender_id, confirmation_message)
        
        if response:
            agent_response = response.get('response_text', '')
            is_ready = response.get('is_ready', False)
            product_interest = response.get('product_interested', '')
            product_ids = response.get('interested_product_ids', [])
            
            print(f"🤖 Agent: {agent_response}")
            print(f"🛍️  Products: {product_interest}")
            print(f"🆔 Product IDs: {product_ids}")
            print(f"🚀 Ready: {is_ready}")
            
            # Analyze confirmation prompt quality
            includes_product_names = any(product in agent_response.lower() for product in [
                'wild stone', 'himalaya', 'neem', 'perfume', 'face wash'
            ])
            
            includes_prices = any(price_indicator in agent_response for price_indicator in [
                '₹', 'price', 'cost', 'total', 'amount'
            ])
            
            confirms_purchase = any(phrase in agent_response.lower() for phrase in [
                'confirm', 'purchase', 'buy', 'order', 'proceed'
            ])
            
            # Should be ready now
            ready_status_correct = is_ready == True
            
            self.log_result(
                "Includes Product Names in Confirmation",
                includes_product_names,
                f"Product names mentioned: {includes_product_names}"
            )
            
            self.log_result(
                "Includes Price Information",
                includes_prices,
                f"Price information included: {includes_prices}"
            )
            
            self.log_result(
                "Purchase Confirmation Language",
                confirms_purchase,
                f"Uses confirmation language: {confirms_purchase}"
            )
            
            self.log_result(
                "is_ready Status After Confirmation",
                ready_status_correct,
                f"is_ready={is_ready} (should be True)"
            )

    def test_5_is_ready_flag_management(self):
        """Test 5: Proper is_ready flag management"""
        self.print_section("TEST 5: is_ready FLAG MANAGEMENT")
        
        sender_id = "test_5_is_ready"
        self.clear_conversation(sender_id)
        
        # Test scenarios that should NOT trigger is_ready=True
        false_scenarios = [
            "I'm looking for perfume",
            "Tell me about Wild Stone",
            "How much does it cost?",
            "That sounds good",
            "I'm interested in this product",
            "It seems perfect for me",
            "I like this one"
        ]
        
        print("🔍 Testing scenarios that should keep is_ready=False:")
        for i, message in enumerate(false_scenarios, 1):
            print(f"\n📝 Test {i}: '{message}'")
            response = self.send_message(sender_id, message)
            
            if response:
                is_ready = response.get('is_ready', False)
                correct = not is_ready
                status = "✅" if correct else "❌"
                
                print(f"   {status} is_ready={is_ready} (should be False)")
                
                self.log_result(
                    f"is_ready False Test {i}",
                    correct,
                    f"Message: '{message}' -> is_ready={is_ready}"
                )
            
            time.sleep(1)
        
        # Test scenarios that SHOULD trigger is_ready=True
        time.sleep(2)
        print("\n🎯 Testing explicit purchase confirmation:")
        
        true_scenarios = [
            "Yes, I want to buy the Wild Stone perfume",
            "I'll take it",
            "I want to purchase this product"
        ]
        
        for i, message in enumerate(true_scenarios, 1):
            print(f"\n📝 Purchase Test {i}: '{message}'")
            response = self.send_message(sender_id, message)
            
            if response:
                is_ready = response.get('is_ready', False)
                correct = is_ready
                status = "✅" if correct else "❌"
                
                print(f"   {status} is_ready={is_ready} (should be True)")
                print(f"   🤖 Response: {response.get('response_text', '')[:80]}...")
                
                self.log_result(
                    f"is_ready True Test {i}",
                    correct,
                    f"Message: '{message}' -> is_ready={is_ready}"
                )
            
            time.sleep(1)

    def test_6_multiple_product_handling(self):
        """Test 6: Multiple product handling"""
        self.print_section("TEST 6: MULTIPLE PRODUCT HANDLING")
        
        sender_id = "test_6_multiple"
        self.clear_conversation(sender_id)
        
        self.print_step(1, "Multiple product selection")
        message1 = "I want Wild Stone perfume and Himalaya neem face wash"
        print(f"👤 Customer: {message1}")
        
        response1 = self.send_message(sender_id, message1)
        
        if response1:
            product_interest = response1.get('product_interested', '')
            product_ids = response1.get('interested_product_ids', [])
            
            print(f"🤖 Agent: {response1.get('response_text', '')[:120]}...")
            print(f"🛍️  Products: {product_interest}")
            print(f"🆔 Product IDs: {product_ids}")
            
            # Check if both products are captured
            has_perfume = 'wild stone' in product_interest.lower() or 'perfume' in product_interest.lower()
            has_face_wash = 'himalaya' in product_interest.lower() or 'neem' in product_interest.lower() or 'face wash' in product_interest.lower()
            has_multiple_ids = len(product_ids) >= 1  # At least some product IDs
            
            self.log_result(
                "Multiple Product Detection - Perfume",
                has_perfume,
                f"Perfume detected in: {product_interest}"
            )
            
            self.log_result(
                "Multiple Product Detection - Face Wash",
                has_face_wash,
                f"Face wash detected in: {product_interest}"
            )
            
            self.log_result(
                "Multiple Product IDs",
                has_multiple_ids,
                f"Product IDs count: {len(product_ids)}"
            )
        
        time.sleep(2)
        
        # Step 2: Add another product
        self.print_step(2, "Adding another product")
        message2 = "I also need a good shampoo for hair fall"
        print(f"👤 Customer: {message2}")
        
        response2 = self.send_message(sender_id, message2)
        
        if response2:
            product_interest = response2.get('product_interested', '')
            product_ids = response2.get('interested_product_ids', [])
            
            print(f"🤖 Agent: {response2.get('response_text', '')[:120]}...")
            print(f"🛍️  Products: {product_interest}")
            print(f"🆔 Product IDs: {product_ids}")
            
            # Check if all three product categories are tracked
            tracks_all_three = all(category in product_interest.lower() for category in ['perfume', 'face wash', 'shampoo']) or \
                              len(product_ids) >= 2
            
            self.log_result(
                "Three Product Categories Tracking",
                tracks_all_three,
                f"All three tracked: {tracks_all_three}"
            )

    def test_7_product_removal_scenarios(self):
        """Test 7: Product removal/modification scenarios"""
        self.print_section("TEST 7: PRODUCT REMOVAL & MODIFICATION SCENARIOS")
        
        sender_id = "test_7_removal"
        self.clear_conversation(sender_id)
        
        # Step 1: Select multiple products
        self.print_step(1, "Initial multiple product selection")
        message1 = "I want Wild Stone perfume, Himalaya face wash, and Head & Shoulders shampoo"
        print(f"👤 Customer: {message1}")
        
        response1 = self.send_message(sender_id, message1)
        initial_products = response1.get('product_interested', '') if response1 else ''
        initial_ids = response1.get('interested_product_ids', []) if response1 else []
        
        print(f"🛍️  Initial Products: {initial_products}")
        print(f"🆔 Initial IDs: {initial_ids}")
        
        time.sleep(2)
        
        # Step 2: Remove one product
        self.print_step(2, "Remove one product")
        message2 = "Actually, I don't need the shampoo anymore"
        print(f"👤 Customer: {message2}")
        
        response2 = self.send_message(sender_id, message2)
        
        if response2:
            updated_products = response2.get('product_interested', '')
            updated_ids = response2.get('interested_product_ids', [])
            
            print(f"🤖 Agent: {response2.get('response_text', '')[:120]}...")
            print(f"🛍️  Updated Products: {updated_products}")
            print(f"🆔 Updated IDs: {updated_ids}")
            
            # Check if shampoo was removed but perfume and face wash remain
            shampoo_removed = 'shampoo' not in updated_products.lower()
            perfume_remains = 'perfume' in updated_products.lower() or 'wild stone' in updated_products.lower()
            face_wash_remains = 'face wash' in updated_products.lower() or 'himalaya' in updated_products.lower()
            
            self.log_result(
                "Product Removal - Shampoo Removed",
                shampoo_removed,
                f"Shampoo removed: {shampoo_removed}"
            )
            
            self.log_result(
                "Product Retention - Perfume Remains",
                perfume_remains,
                f"Perfume remains: {perfume_remains}"
            )
            
            self.log_result(
                "Product Retention - Face Wash Remains",
                face_wash_remains,
                f"Face wash remains: {face_wash_remains}"
            )
        
        time.sleep(2)
        
        # Step 3: Replace a product
        self.print_step(3, "Replace a product")
        message3 = "Can I change the face wash to something for sensitive skin instead?"
        print(f"👤 Customer: {message3}")
        
        response3 = self.send_message(sender_id, message3)
        
        if response3:
            final_products = response3.get('product_interested', '')
            final_ids = response3.get('interested_product_ids', [])
            
            print(f"🤖 Agent: {response3.get('response_text', '')[:120]}...")
            print(f"🛍️  Final Products: {final_products}")
            print(f"🆔 Final IDs: {final_ids}")
            
            # Check if system understood the replacement request
            understands_replacement = 'sensitive' in response3.get('response_text', '').lower()
            
            self.log_result(
                "Product Replacement Understanding",
                understands_replacement,
                f"Understands sensitive skin request: {understands_replacement}"
            )

    def test_8_system_flow_analysis(self):
        """Test 8: Overall system flow analysis"""
        self.print_section("TEST 8: OVERALL SYSTEM FLOW ANALYSIS")
        
        # Complete end-to-end flow
        sender_id = "test_8_complete_flow"
        self.clear_conversation(sender_id)
        
        complete_flow = [
            {"msg": "Hi, I'm looking for beauty products", "expect_ready": False},
            {"msg": "I need a perfume that lasts all day", "expect_ready": False},
            {"msg": "Wild Stone sounds good, what's the price?", "expect_ready": False},
            {"msg": "I also need a face wash for oily skin", "expect_ready": False},
            {"msg": "Show me what you have for face wash", "expect_ready": False},
            {"msg": "Perfect, I want both the perfume and face wash", "expect_ready": False},
            {"msg": "Yes, confirm my order for both products", "expect_ready": True}
        ]
        
        flow_success = True
        conversation_quality = []
        
        for i, step in enumerate(complete_flow, 1):
            print(f"\n📝 Flow Step {i}: {step['msg']}")
            response = self.send_message(sender_id, step['msg'])
            
            if response:
                is_ready = response.get('is_ready', False)
                agent_response = response.get('response_text', '')
                
                print(f"🤖 Agent: {agent_response[:100]}...")
                print(f"🚀 Ready: {is_ready} (Expected: {step['expect_ready']})")
                
                # Check is_ready correctness
                ready_correct = is_ready == step['expect_ready']
                if not ready_correct:
                    flow_success = False
                
                # Analyze response quality
                quality_metrics = {
                    'length': len(agent_response) > 30,
                    'relevant': any(word in agent_response.lower() for word in ['perfume', 'face wash', 'beauty', 'skin', 'product']),
                    'helpful': any(word in agent_response.lower() for word in ['help', 'recommend', 'suggest', 'perfect', 'great'])
                }
                
                conversation_quality.append(quality_metrics)
                
                self.log_result(
                    f"Complete Flow Step {i}",
                    ready_correct,
                    f"is_ready={is_ready}, expected={step['expect_ready']}"
                )
            else:
                flow_success = False
            
            time.sleep(1.5)
        
        # Analyze overall conversation quality
        avg_quality = sum(sum(metrics.values()) for metrics in conversation_quality) / (len(conversation_quality) * 3)
        
        self.log_result(
            "Complete Flow Success",
            flow_success,
            f"All is_ready flags correct: {flow_success}"
        )
        
        self.log_result(
            "Conversation Quality",
            avg_quality > 0.7,
            f"Average quality score: {avg_quality:.2f}"
        )

    def analyze_langchain_potential(self):
        """Analyze potential improvements with LangChain"""
        self.print_section("LANGCHAIN ANALYSIS & RECOMMENDATIONS")
        
        print("🔍 Current System Analysis:")
        print("=" * 50)
        print("✅ Strengths:")
        print("   • Direct Azure OpenAI integration")
        print("   • Custom business context prompting")
        print("   • Product matching with similarity scoring")
        print("   • Conversation history management")
        print("   • Sales stage analysis")
        
        print("\n❌ Current Limitations:")
        print("   • Manual prompt engineering for each function")
        print("   • No structured conversation flow management")
        print("   • Limited memory and context persistence")
        print("   • Basic product removal/modification handling")
        print("   • No advanced conversation state management")
        
        print("\n🚀 LangChain Potential Improvements:")
        print("=" * 50)
        
        improvements = [
            {
                "area": "Conversation Memory",
                "current": "Manual conversation history in MongoDB",
                "langchain": "ConversationBufferWindowMemory, ConversationSummaryMemory",
                "benefit": "Better context retention, automatic summarization"
            },
            {
                "area": "Product State Management", 
                "current": "Basic product interest tracking",
                "langchain": "Custom ConversationEntityMemory",
                "benefit": "Track product additions/removals with entity memory"
            },
            {
                "area": "Sales Flow Management",
                "current": "Manual sales stage analysis",
                "langchain": "StateGraph with sales stages as nodes",
                "benefit": "Structured flow, automatic stage transitions"
            },
            {
                "area": "Prompt Management",
                "current": "Hardcoded prompts in Python strings",
                "langchain": "PromptTemplate, ChatPromptTemplate",
                "benefit": "Reusable, testable, version-controlled prompts"
            },
            {
                "area": "Response Generation",
                "current": "Single LLM call with complex prompt",
                "langchain": "Chain-of-Thought, ReAct agents",
                "benefit": "Better reasoning, step-by-step decision making"
            },
            {
                "area": "Product Retrieval",
                "current": "LLM-based similarity matching",
                "langchain": "Vector stores + semantic search",
                "benefit": "Faster, more accurate product matching"
            }
        ]
        
        for improvement in improvements:
            print(f"\n🎯 {improvement['area']}:")
            print(f"   Current: {improvement['current']}")
            print(f"   LangChain: {improvement['langchain']}")
            print(f"   Benefit: {improvement['benefit']}")
        
        print(f"\n{Colors.HEADER}🏗️  RECOMMENDED LANGCHAIN ARCHITECTURE:{Colors.ENDC}")
        print("=" * 50)
        print("""
1. **ConversationChain with Memory**
   - ConversationBufferWindowMemory for recent context
   - ConversationEntityMemory for product tracking
   
2. **StateGraph for Sales Funnel**
   - Nodes: Interest → Discovery → Evaluation → Confirmation → Handover
   - Conditional edges based on customer intent
   
3. **Vector Database Integration**
   - Embed product descriptions and tags
   - Semantic similarity search instead of LLM matching
   
4. **Structured Output Parsing**
   - Pydantic models for consistent API responses
   - Output parsers for is_ready, product_ids extraction
   
5. **Tool Integration**
   - Product database tool
   - Price calculation tool
   - Inventory check tool
        """)

    def generate_summary_report(self):
        """Generate comprehensive test summary"""
        self.print_section("TEST SUMMARY REPORT")
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['passed'])
        failed_tests = total_tests - passed_tests
        
        pass_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        print(f"📊 **OVERALL RESULTS**")
        print(f"   Total Tests: {total_tests}")
        print(f"   ✅ Passed: {passed_tests}")
        print(f"   ❌ Failed: {failed_tests}")
        print(f"   📈 Pass Rate: {pass_rate:.1f}%")
        
        if failed_tests > 0:
            print(f"\n❌ **FAILED TESTS:**")
            for result in self.test_results:
                if not result['passed']:
                    print(f"   • {result['test_name']}: {result['details']}")
        
        print(f"\n🎯 **KEY FINDINGS:**")
        findings = []
        
        # Analyze specific areas
        is_ready_tests = [r for r in self.test_results if 'is_ready' in r['test_name'].lower()]
        is_ready_success = sum(1 for r in is_ready_tests if r['passed']) / len(is_ready_tests) * 100 if is_ready_tests else 0
        
        product_tests = [r for r in self.test_results if 'product' in r['test_name'].lower()]
        product_success = sum(1 for r in product_tests if r['passed']) / len(product_tests) * 100 if product_tests else 0
        
        response_tests = [r for r in self.test_results if 'response' in r['test_name'].lower() or 'quality' in r['test_name'].lower()]
        response_success = sum(1 for r in response_tests if r['passed']) / len(response_tests) * 100 if response_tests else 0
        
        print(f"   • is_ready Flag Management: {is_ready_success:.1f}% success")
        print(f"   • Product Detection & Matching: {product_success:.1f}% success")
        print(f"   • Response Quality: {response_success:.1f}% success")
        
        print(f"\n💡 **RECOMMENDATIONS:**")
        if is_ready_success < 80:
            print("   • Improve is_ready flag logic with more explicit purchase confirmation detection")
        if product_success < 80:
            print("   • Enhance product matching and multiple product handling")
        if response_success < 80:
            print("   • Improve response quality and natural conversation flow")
        
        print("   • Consider LangChain integration for better conversation state management")
        print("   • Implement vector database for faster product matching")
        print("   • Add structured sales funnel with state transitions")

    def run_all_tests(self):
        """Run all comprehensive tests"""
        print(f"{Colors.HEADER}{Colors.BOLD}")
        print("🧪 COMPREHENSIVE CONVERSATION & HANDOVER TEST SUITE")
        print("🎯 Testing complete sales agent conversation flow")
        print("🤖 Analyzing LLM response quality and purchase handover process")
        print(f"{'=' * 80}{Colors.ENDC}\n")
        
        # Check API health
        try:
            health_response = requests.get(HEALTH_URL, timeout=10)
            if health_response.status_code != 200:
                print(f"{Colors.FAIL}❌ API Health Check Failed{Colors.ENDC}")
                return
        except:
            print(f"{Colors.FAIL}❌ Cannot connect to API at {API_BASE_URL}{Colors.ENDC}")
            return
        
        print(f"{Colors.OKGREEN}✅ API Health Check Passed{Colors.ENDC}\n")
        
        # Run all tests
        self.test_1_random_customer_inquiries()
        self.test_2_product_navigation_and_matching()
        self.test_3_conversation_continuity()
        self.test_4_purchase_confirmation_prompts()
        self.test_5_is_ready_flag_management()
        self.test_6_multiple_product_handling()
        self.test_7_product_removal_scenarios()
        self.test_8_system_flow_analysis()
        
        # Analysis and reporting
        self.analyze_langchain_potential()
        self.generate_summary_report()
        
        # Save detailed logs
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        with open(f"test_results_{timestamp}.json", "w") as f:
            json.dump({
                "test_results": self.test_results,
                "conversation_logs": self.conversation_logs,
                "timestamp": timestamp
            }, f, indent=2)
        
        print(f"\n📄 Detailed results saved to: test_results_{timestamp}.json")

if __name__ == "__main__":
    tester = ConversationHandoverTester()
    tester.run_all_tests()
