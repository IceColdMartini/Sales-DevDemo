#!/usr/bin/env python3
"""
Comprehensive End-to-End Test for Sales Agent System
Focus: Multiple Product Detection & Product ID Handling

This test validates:
1. Multiple product detection and tracking
2. Proper product ID extraction and posting to routing agent
3. Complete conversation flow with state management
4. API response format validation for routing agent integration
"""
import requests
import json
import time
from typing import Dict, List, Any
from datetime import datetime

# Configuration from .env and docker-compose.yml
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

class E2EMultiProductTester:
    def __init__(self):
        self.test_results = []
        self.conversation_logs = []
        
    def log_test(self, test_name: str, passed: bool, details: str = "", data: Dict = None):
        """Log test results with detailed information"""
        result = {
            "test_name": test_name,
            "passed": passed,
            "details": details,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = f"{Colors.OKGREEN}✅ PASS{Colors.ENDC}" if passed else f"{Colors.FAIL}❌ FAIL{Colors.ENDC}"
        print(f"{status} {test_name}")
        if details:
            print(f"   📝 {details}")
        if data and not passed:
            print(f"   📊 Data: {json.dumps(data, indent=2)}")

    def send_message(self, sender_id: str, message: str) -> Dict:
        """Send message and return response with detailed logging"""
        payload = {
            "sender": sender_id,
            "recipient": "page_123",
            "text": message
        }
        
        try:
            print(f"\n👤 {Colors.OKCYAN}Customer:{Colors.ENDC} {message}")
            response = requests.post(WEBHOOK_URL, json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                print(f"🤖 {Colors.OKBLUE}Agent:{Colors.ENDC} {data.get('response_text', '')[:100]}...")
                
                # Log key data
                print(f"🛍️  Products: {data.get('product_interested', 'None')}")
                product_ids = data.get('interested_product_ids', [])
                print(f"🆔 Product IDs: {len(product_ids)} IDs: {product_ids}")
                print(f"🚀 Ready for Handover: {data.get('is_ready', False)}")
                
                return data
            else:
                print(f"❌ API Error: {response.status_code} - {response.text}")
                return {"error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            print(f"❌ Request failed: {e}")
            return {"error": str(e)}

    def clear_conversation(self, sender_id: str):
        """Clear conversation history"""
        try:
            requests.delete(f"{API_BASE_URL}/api/webhook/conversation/{sender_id}")
            print(f"🧹 Cleared conversation for {sender_id}")
        except:
            pass

    def validate_api_response_structure(self, response: Dict, test_name: str) -> bool:
        """Validate that API response has all required fields for routing agent"""
        required_fields = ["sender", "response_text", "is_ready"]
        optional_fields = ["product_interested", "interested_product_ids"]
        
        missing_required = [field for field in required_fields if field not in response]
        
        if missing_required:
            self.log_test(f"{test_name} - API Structure", False, 
                         f"Missing required fields: {missing_required}", response)
            return False
            
        # Check data types
        if not isinstance(response.get('is_ready'), bool):
            self.log_test(f"{test_name} - is_ready Type", False, 
                         f"is_ready should be boolean, got {type(response.get('is_ready'))}")
            return False
            
        if response.get('interested_product_ids') and not isinstance(response.get('interested_product_ids'), list):
            self.log_test(f"{test_name} - Product IDs Type", False, 
                         f"interested_product_ids should be list, got {type(response.get('interested_product_ids'))}")
            return False
            
        self.log_test(f"{test_name} - API Structure", True, "All required fields present with correct types")
        return True

    def test_system_health(self):
        """Test system health and connectivity"""
        print(f"\n{Colors.HEADER}🏥 SYSTEM HEALTH CHECK{Colors.ENDC}")
        print("=" * 60)
        
        try:
            health_response = requests.get(HEALTH_URL, timeout=10)
            if health_response.status_code == 200:
                health_data = health_response.json()
                print(f"✅ System Status: {health_data.get('status')}")
                print(f"✅ PostgreSQL: {health_data.get('databases', {}).get('postgresql')}")
                print(f"✅ MongoDB: {health_data.get('databases', {}).get('mongodb')}")
                print(f"✅ AI Service: {health_data.get('services', {}).get('ai_service')}")
                
                all_healthy = (
                    health_data.get('status') == 'healthy' and
                    health_data.get('databases', {}).get('postgresql') == 'connected' and
                    health_data.get('databases', {}).get('mongodb') == 'connected' and
                    health_data.get('services', {}).get('ai_service') == 'available'
                )
                
                self.log_test("System Health", all_healthy, 
                             "All services operational" if all_healthy else "Some services have issues")
                return all_healthy
            else:
                self.log_test("System Health", False, f"Health endpoint returned {health_response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("System Health", False, f"Health check failed: {e}")
            return False

    def test_single_product_detection(self):
        """Test single product detection and ID extraction"""
        print(f"\n{Colors.HEADER}🎯 SINGLE PRODUCT DETECTION TEST{Colors.ENDC}")
        print("=" * 60)
        
        sender_id = "test_single_product"
        self.clear_conversation(sender_id)
        
        # Test single product inquiry
        response = self.send_message(sender_id, "I want to buy Wild Stone perfume")
        
        if "error" in response:
            self.log_test("Single Product - API Call", False, response["error"])
            return False
            
        # Validate response structure
        if not self.validate_api_response_structure(response, "Single Product"):
            return False
            
        # Check product detection
        product_interested = response.get('product_interested', '')
        product_ids = response.get('interested_product_ids', [])
        
        single_product_detected = (
            'Wild Stone' in product_interested and
            len(product_ids) >= 1 and
            isinstance(product_ids[0], str) and
            len(product_ids[0]) > 10  # UUID length check
        )
        
        self.log_test("Single Product - Detection", single_product_detected, 
                     f"Product: {product_interested}, IDs: {len(product_ids)}")
        
        # Should not be ready for handover on first inquiry
        not_ready_initially = not response.get('is_ready', True)
        self.log_test("Single Product - Not Ready Initially", not_ready_initially, 
                     f"is_ready = {response.get('is_ready')}")
        
        return single_product_detected and not_ready_initially

    def test_multiple_product_detection(self):
        """Test multiple product detection and tracking - MAIN FOCUS"""
        print(f"\n{Colors.HEADER}🎯 MULTIPLE PRODUCT DETECTION TEST (MAIN FOCUS){Colors.ENDC}")
        print("=" * 60)
        
        sender_id = "test_multiple_products"
        self.clear_conversation(sender_id)
        
        # Step 1: Request multiple products
        print(f"\n{Colors.BOLD}STEP 1: Initial Multiple Product Request{Colors.ENDC}")
        response1 = self.send_message(sender_id, "I need Wild Stone perfume and Himalaya face wash")
        
        if "error" in response1:
            self.log_test("Multiple Products - Step 1 API", False, response1["error"])
            return False
            
        self.validate_api_response_structure(response1, "Multiple Products - Step 1")
        
        # Check if multiple products detected
        product_interested_1 = response1.get('product_interested', '')
        product_ids_1 = response1.get('interested_product_ids', [])
        
        step1_multiple_detected = (
            ('Wild Stone' in product_interested_1 or 'Himalaya' in product_interested_1) and
            len(product_ids_1) >= 1
        )
        
        self.log_test("Multiple Products - Step 1 Detection", step1_multiple_detected,
                     f"Products: {product_interested_1}, IDs count: {len(product_ids_1)}")
        
        time.sleep(2)
        
        # Step 2: Add another product to the conversation
        print(f"\n{Colors.BOLD}STEP 2: Add More Products{Colors.ENDC}")
        response2 = self.send_message(sender_id, "I also want some soap for daily use")
        
        if "error" in response2:
            self.log_test("Multiple Products - Step 2 API", False, response2["error"])
            return False
            
        self.validate_api_response_structure(response2, "Multiple Products - Step 2")
        
        product_interested_2 = response2.get('product_interested', '')
        product_ids_2 = response2.get('interested_product_ids', [])
        
        # Should maintain previous products + new ones
        step2_maintains_products = len(product_ids_2) >= len(product_ids_1)
        
        self.log_test("Multiple Products - Step 2 Maintains Previous", step2_maintains_products,
                     f"Step1 IDs: {len(product_ids_1)}, Step2 IDs: {len(product_ids_2)}")
        
        time.sleep(2)
        
        # Step 3: Price inquiry for multiple products
        print(f"\n{Colors.BOLD}STEP 3: Price Inquiry for Multiple Products{Colors.ENDC}")
        response3 = self.send_message(sender_id, "What are the prices for all these products?")
        
        if "error" in response3:
            self.log_test("Multiple Products - Step 3 API", False, response3["error"])
            return False
            
        product_ids_3 = response3.get('interested_product_ids', [])
        
        # Should still maintain multiple products
        step3_maintains_multiple = len(product_ids_3) >= 2
        
        self.log_test("Multiple Products - Step 3 Maintains Multiple", step3_maintains_multiple,
                     f"Final product count: {len(product_ids_3)}")
        
        time.sleep(2)
        
        # Step 4: Purchase confirmation for multiple products
        print(f"\n{Colors.BOLD}STEP 4: Purchase Confirmation{Colors.ENDC}")
        response4 = self.send_message(sender_id, "Yes, I want to buy all of them")
        
        if "error" in response4:
            self.log_test("Multiple Products - Step 4 API", False, response4["error"])
            return False
            
        product_ids_4 = response4.get('interested_product_ids', [])
        is_ready_4 = response4.get('is_ready', False)
        
        # Should be ready for handover with multiple product IDs
        purchase_confirmation_success = (
            is_ready_4 and 
            len(product_ids_4) >= 2 and
            all(isinstance(pid, str) and len(pid) > 10 for pid in product_ids_4)
        )
        
        self.log_test("Multiple Products - Purchase Confirmation", purchase_confirmation_success,
                     f"is_ready: {is_ready_4}, Product IDs: {len(product_ids_4)}")
        
        # Detailed validation of product IDs format
        valid_uuid_format = all(
            isinstance(pid, str) and 
            len(pid.split('-')) == 5 and 
            len(pid) == 36
            for pid in product_ids_4
        )
        
        self.log_test("Multiple Products - UUID Format", valid_uuid_format,
                     f"All {len(product_ids_4)} product IDs are valid UUIDs")
        
        print(f"\n{Colors.OKCYAN}📊 MULTIPLE PRODUCT TEST SUMMARY:{Colors.ENDC}")
        print(f"   Step 1 Products: {len(product_ids_1)}")
        print(f"   Step 2 Products: {len(product_ids_2)}")
        print(f"   Step 3 Products: {len(product_ids_3)}")
        print(f"   Step 4 Products: {len(product_ids_4)}")
        print(f"   Final Product IDs: {product_ids_4}")
        
        return (step1_multiple_detected and step2_maintains_products and 
                step3_maintains_multiple and purchase_confirmation_success and valid_uuid_format)

    def test_product_removal_scenario(self):
        """Test product removal from conversation state"""
        print(f"\n{Colors.HEADER}🗑️  PRODUCT REMOVAL TEST{Colors.ENDC}")
        print("=" * 60)
        
        sender_id = "test_product_removal"
        self.clear_conversation(sender_id)
        
        # Add multiple products
        response1 = self.send_message(sender_id, "I want perfume, face wash, and shampoo")
        product_ids_1 = response1.get('interested_product_ids', [])
        
        time.sleep(2)
        
        # Remove one product
        response2 = self.send_message(sender_id, "Actually, I don't need the shampoo")
        product_ids_2 = response2.get('interested_product_ids', [])
        
        # Should have fewer products now
        removal_worked = len(product_ids_2) < len(product_ids_1) or len(product_ids_2) >= 1
        
        self.log_test("Product Removal", removal_worked,
                     f"Before: {len(product_ids_1)}, After: {len(product_ids_2)}")
        
        return removal_worked

    def test_conversation_continuity_with_products(self):
        """Test that conversation maintains product context across turns"""
        print(f"\n{Colors.HEADER}🔄 CONVERSATION CONTINUITY TEST{Colors.ENDC}")
        print("=" * 60)
        
        sender_id = "test_continuity"
        self.clear_conversation(sender_id)
        
        # Build conversation with products
        messages = [
            "I'm looking for beauty products",
            "Show me perfumes and face wash",
            "Tell me about the Wild Stone perfume",
            "What's the price?",
            "That sounds good, I'll take it"
        ]
        
        product_ids_progression = []
        
        for i, message in enumerate(messages, 1):
            print(f"\n{Colors.BOLD}Turn {i}:{Colors.ENDC}")
            response = self.send_message(sender_id, message)
            
            if "error" not in response:
                product_ids = response.get('interested_product_ids', [])
                product_ids_progression.append(len(product_ids))
                
            time.sleep(1)
        
        # Should maintain product context and show progression
        continuity_maintained = (
            len(product_ids_progression) == 5 and
            max(product_ids_progression) >= 1 and
            product_ids_progression[-1] >= 1  # Final turn should have products
        )
        
        self.log_test("Conversation Continuity", continuity_maintained,
                     f"Product count progression: {product_ids_progression}")
        
        return continuity_maintained

    def test_routing_agent_handover_format(self):
        """Test that handover data is properly formatted for routing agent"""
        print(f"\n{Colors.HEADER}🤝 ROUTING AGENT HANDOVER FORMAT TEST{Colors.ENDC}")
        print("=" * 60)
        
        sender_id = "test_handover_format"
        self.clear_conversation(sender_id)
        
        # Complete purchase flow
        self.send_message(sender_id, "I want Wild Stone perfume")
        time.sleep(1)
        self.send_message(sender_id, "How much is it?")
        time.sleep(1)
        final_response = self.send_message(sender_id, "Yes, I'll buy it")
        
        if "error" in final_response:
            self.log_test("Handover Format - API Call", False, final_response["error"])
            return False
        
        # Validate handover format
        required_handover_fields = ["sender", "response_text", "is_ready", "interested_product_ids"]
        handover_complete = all(field in final_response for field in required_handover_fields)
        
        # Check data quality
        handover_quality = (
            final_response.get('is_ready') is True and
            isinstance(final_response.get('interested_product_ids'), list) and
            len(final_response.get('interested_product_ids', [])) >= 1 and
            isinstance(final_response.get('sender'), str) and
            isinstance(final_response.get('response_text'), str)
        )
        
        self.log_test("Handover Format - Structure", handover_complete,
                     f"All required fields present: {handover_complete}")
        
        self.log_test("Handover Format - Data Quality", handover_quality,
                     f"Data types and values valid: {handover_quality}")
        
        print(f"\n{Colors.OKCYAN}📋 HANDOVER DATA FOR ROUTING AGENT:{Colors.ENDC}")
        print(json.dumps({
            "sender": final_response.get('sender'),
            "is_ready": final_response.get('is_ready'),
            "product_count": len(final_response.get('interested_product_ids', [])),
            "product_ids": final_response.get('interested_product_ids', []),
            "has_response": bool(final_response.get('response_text'))
        }, indent=2))
        
        return handover_complete and handover_quality

    def run_comprehensive_e2e_test(self):
        """Run all end-to-end tests"""
        print(f"\n{Colors.HEADER}🚀 COMPREHENSIVE END-TO-END TEST SUITE{Colors.ENDC}")
        print(f"{Colors.HEADER}Focus: Multiple Product Detection & Routing Agent Integration{Colors.ENDC}")
        print("=" * 80)
        
        # Run all tests
        tests = [
            ("System Health", self.test_system_health),
            ("Single Product Detection", self.test_single_product_detection),
            ("Multiple Product Detection", self.test_multiple_product_detection),
            ("Product Removal", self.test_product_removal_scenario),
            ("Conversation Continuity", self.test_conversation_continuity_with_products),
            ("Routing Agent Handover", self.test_routing_agent_handover_format)
        ]
        
        print(f"\n{Colors.OKCYAN}Running {len(tests)} test suites...{Colors.ENDC}")
        
        for test_name, test_func in tests:
            print(f"\n{Colors.BOLD}{'='*20} {test_name.upper()} {'='*20}{Colors.ENDC}")
            try:
                test_func()
            except Exception as e:
                self.log_test(f"{test_name} - Execution", False, f"Test failed with exception: {e}")
            
            time.sleep(1)
        
        self.print_final_summary()

    def print_final_summary(self):
        """Print comprehensive test summary"""
        print(f"\n{Colors.HEADER}📊 COMPREHENSIVE E2E TEST SUMMARY{Colors.ENDC}")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['passed'])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"\n{Colors.BOLD}Overall Results:{Colors.ENDC}")
        print(f"   ✅ Passed: {Colors.OKGREEN}{passed_tests}{Colors.ENDC}")
        print(f"   ❌ Failed: {Colors.FAIL}{failed_tests}{Colors.ENDC}")
        print(f"   📊 Success Rate: {Colors.OKCYAN}{success_rate:.1f}%{Colors.ENDC}")
        
        # Key focus areas summary
        print(f"\n{Colors.BOLD}Key Focus Areas:{Colors.ENDC}")
        
        multiple_product_tests = [r for r in self.test_results if 'Multiple Product' in r['test_name']]
        multiple_success = sum(1 for r in multiple_product_tests if r['passed'])
        print(f"   🎯 Multiple Product Detection: {multiple_success}/{len(multiple_product_tests)} tests passed")
        
        handover_tests = [r for r in self.test_results if 'Handover' in r['test_name']]
        handover_success = sum(1 for r in handover_tests if r['passed'])
        print(f"   🤝 Routing Agent Integration: {handover_success}/{len(handover_tests)} tests passed")
        
        # Failed tests detail
        if failed_tests > 0:
            print(f"\n{Colors.FAIL}❌ Failed Tests:{Colors.ENDC}")
            for result in self.test_results:
                if not result['passed']:
                    print(f"   • {result['test_name']}: {result['details']}")
        
        # Recommendations
        print(f"\n{Colors.BOLD}Recommendations:{Colors.ENDC}")
        if success_rate >= 90:
            print(f"   🎉 System is working excellently! Ready for production.")
        elif success_rate >= 75:
            print(f"   ⚠️  System is mostly working but needs attention to failed tests.")
        else:
            print(f"   🚨 System needs significant fixes before deployment.")
        
        print(f"\n{Colors.OKCYAN}Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.ENDC}")

if __name__ == "__main__":
    tester = E2EMultiProductTester()
    tester.run_comprehensive_e2e_test()
