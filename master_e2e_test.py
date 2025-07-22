#!/usr/bin/env python3
"""
Master End-to-End Test Script for Sales Agent Microservice
Tests the complete workflow from customer inquiry to purchase readiness

This script tests:
1. API connectivity and health
2. Database connections (PostgreSQL and MongoDB)
3. Product database queries and matching
4. Conversation storage and retrieval
5. AI response generation
6. Sales funnel progression
7. Purchase readiness detection
8. Proper handover data for routing agent
"""

import requests
import time
import json
import pymongo
import psycopg2
from typing import Dict, List, Optional
from datetime import datetime
import sys
import os

# Configuration
API_BASE_URL = "http://localhost:8000"
WEBHOOK_URL = f"{API_BASE_URL}/api/webhook"

# Database configurations
POSTGRES_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "sales_db",
    "user": "user",
    "password": "password"
}

MONGO_CONFIG = {
    "uri": "mongodb://localhost:27017/",
    "database": "conversations_db"
}

class Colors:
    """ANSI color codes for console output"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

class E2ETestRunner:
    def __init__(self):
        self.postgres_conn = None
        self.mongo_client = None
        self.test_results = {
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "errors": []
        }
        
    def log_test(self, test_name: str, passed: bool, message: str = ""):
        """Log test results"""
        self.test_results["total_tests"] += 1
        if passed:
            self.test_results["passed"] += 1
            print(f"{Colors.OKGREEN}✅ {test_name}: PASSED{Colors.ENDC}")
            if message:
                print(f"   {message}")
        else:
            self.test_results["failed"] += 1
            error_msg = f"{test_name}: FAILED - {message}"
            self.test_results["errors"].append(error_msg)
            print(f"{Colors.FAIL}❌ {test_name}: FAILED{Colors.ENDC}")
            if message:
                print(f"   {Colors.FAIL}{message}{Colors.ENDC}")

    def print_header(self, title: str):
        """Print a formatted header"""
        print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}{title.center(80)}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}")

    def print_section(self, title: str):
        """Print a formatted section header"""
        print(f"\n{Colors.OKBLUE}{Colors.BOLD}📋 {title}{Colors.ENDC}")
        print(f"{Colors.OKBLUE}{'-' * (len(title) + 4)}{Colors.ENDC}")

    def connect_databases(self):
        """Test database connections"""
        self.print_section("DATABASE CONNECTIVITY TESTS")
        
        # Test PostgreSQL connection
        try:
            self.postgres_conn = psycopg2.connect(**POSTGRES_CONFIG)
            cursor = self.postgres_conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM products;")
            product_count = cursor.fetchone()[0]
            cursor.close()
            
            self.log_test("PostgreSQL Connection", True, f"Connected successfully, {product_count} products in database")
        except Exception as e:
            self.log_test("PostgreSQL Connection", False, str(e))
            
        # Test MongoDB connection
        try:
            self.mongo_client = pymongo.MongoClient(MONGO_CONFIG["uri"])
            db = self.mongo_client[MONGO_CONFIG["database"]]
            # Test connection by listing collections
            collections = db.list_collection_names()
            self.log_test("MongoDB Connection", True, f"Connected successfully, collections: {collections}")
        except Exception as e:
            self.log_test("MongoDB Connection", False, str(e))

    def test_api_health(self):
        """Test API health and endpoints"""
        self.print_section("API HEALTH TESTS")
        
        try:
            response = requests.get(f"{API_BASE_URL}/health", timeout=10)
            if response.status_code == 200:
                self.log_test("API Health Check", True, f"Status: {response.status_code}")
            else:
                self.log_test("API Health Check", False, f"Unexpected status: {response.status_code}")
        except Exception as e:
            self.log_test("API Health Check", False, str(e))

    def send_message(self, sender_id: str, message: str) -> Optional[Dict]:
        """Send a message to the sales agent"""
        payload = {
            "sender": sender_id,
            "recipient": "test_page",
            "text": message
        }
        
        try:
            response = requests.post(WEBHOOK_URL, json=payload, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"   {Colors.FAIL}Failed to send message: {e}{Colors.ENDC}")
            return None

    def clear_conversation(self, sender_id: str) -> bool:
        """Clear conversation history for a user"""
        try:
            response = requests.delete(f"{API_BASE_URL}/api/webhook/conversation/{sender_id}")
            return response.status_code == 200
        except Exception as e:
            print(f"   {Colors.WARNING}Failed to clear conversation: {e}{Colors.ENDC}")
            return False

    def verify_conversation_storage(self, sender_id: str) -> bool:
        """Verify conversation is stored in MongoDB"""
        if not self.mongo_client:
            return False
            
        try:
            db = self.mongo_client[MONGO_CONFIG["database"]]
            conversation = db.conversations.find_one({"sender_id": sender_id})
            return conversation is not None
        except Exception as e:
            print(f"   {Colors.FAIL}MongoDB verification failed: {e}{Colors.ENDC}")
            return False

    def verify_product_data(self, response: Dict) -> Dict:
        """Verify product data in response"""
        results = {
            "product_interested": False,
            "product_ids": False,
            "valid_ids": False
        }
        
        # Check if product_interested is present
        if response.get('product_interested'):
            results["product_interested"] = True
            
        # Check if interested_product_ids is present
        if response.get('interested_product_ids'):
            results["product_ids"] = True
            
            # Verify product IDs exist in database
            if self.postgres_conn:
                try:
                    cursor = self.postgres_conn.cursor()
                    product_ids = response.get('interested_product_ids', [])
                    if product_ids:
                        placeholders = ','.join(['%s'] * len(product_ids))
                        cursor.execute(f"SELECT id FROM products WHERE id IN ({placeholders})", product_ids)
                        found_ids = [row[0] for row in cursor.fetchall()]
                        cursor.close()
                        
                        if len(found_ids) == len(product_ids):
                            results["valid_ids"] = True
                except Exception as e:
                    print(f"   {Colors.WARNING}Product ID verification failed: {e}{Colors.ENDC}")
                    
        return results

    def test_product_discovery_workflow(self):
        """Test complete product discovery workflow"""
        self.print_section("PRODUCT DISCOVERY WORKFLOW")
        
        sender_id = "e2e_test_discovery"
        self.clear_conversation(sender_id)
        
        # Test 1: Initial product inquiry
        print(f"\n{Colors.OKCYAN}👤 Customer: I'm looking for a good perfume{Colors.ENDC}")
        response = self.send_message(sender_id, "I'm looking for a good perfume")
        
        if response:
            print(f"🤖 Agent: {response.get('response_text', 'No response')[:150]}...")
            
            # Verify response structure
            has_response = bool(response.get('response_text'))
            self.log_test("Initial Inquiry Response", has_response, "Agent provided response text")
            
            # Should not be ready yet
            is_ready = response.get('is_ready', False)
            self.log_test("Initial Inquiry Readiness", not is_ready, f"is_ready={is_ready} (should be False)")
            
            # Verify conversation storage
            time.sleep(1)  # Allow time for storage
            conversation_stored = self.verify_conversation_storage(sender_id)
            self.log_test("Conversation Storage", conversation_stored, "Conversation saved to MongoDB")
        else:
            self.log_test("Initial Inquiry Response", False, "No response received")

        time.sleep(2)

        # Test 2: Specific product inquiry
        print(f"\n{Colors.OKCYAN}👤 Customer: Tell me about Wild Stone perfume{Colors.ENDC}")
        response = self.send_message(sender_id, "Tell me about Wild Stone perfume")
        
        if response:
            print(f"🤖 Agent: {response.get('response_text', 'No response')[:150]}...")
            
            # Verify product matching
            product_data = self.verify_product_data(response)
            self.log_test("Product Interest Detection", product_data["product_interested"], 
                         f"product_interested: {response.get('product_interested', 'None')}")
            self.log_test("Product IDs Provided", product_data["product_ids"],
                         f"interested_product_ids: {response.get('interested_product_ids', 'None')}")
            self.log_test("Valid Product IDs", product_data["valid_ids"],
                         "Product IDs exist in database")
            
            # Should still not be ready
            is_ready = response.get('is_ready', False)
            self.log_test("Product Inquiry Readiness", not is_ready, f"is_ready={is_ready} (should be False)")

        time.sleep(2)

    def test_price_inquiry_workflow(self):
        """Test price inquiry and handling"""
        self.print_section("PRICE INQUIRY WORKFLOW")
        
        sender_id = "e2e_test_pricing"
        self.clear_conversation(sender_id)
        
        # Build context first
        self.send_message(sender_id, "I want a perfume")
        time.sleep(1)
        self.send_message(sender_id, "Tell me about Wild Stone perfume")
        time.sleep(1)
        
        # Test price inquiry
        print(f"\n{Colors.OKCYAN}👤 Customer: How much does it cost?{Colors.ENDC}")
        response = self.send_message(sender_id, "How much does it cost?")
        
        if response:
            print(f"🤖 Agent: {response.get('response_text', 'No response')[:200]}...")
            
            # Check if price information is provided
            response_text = response.get('response_text', '')
            has_price_info = any(symbol in response_text for symbol in ['₹', 'Rs', 'price', 'cost', 'rupees'])
            self.log_test("Price Information Provided", has_price_info, 
                         "Response contains pricing information")
            
            # Should still not be ready
            is_ready = response.get('is_ready', False)
            self.log_test("Price Inquiry Readiness", not is_ready, f"is_ready={is_ready} (should be False)")

    def test_purchase_confirmation_workflow(self):
        """Test purchase confirmation and readiness detection"""
        self.print_section("PURCHASE CONFIRMATION WORKFLOW")
        
        sender_id = "e2e_test_purchase"
        self.clear_conversation(sender_id)
        
        # Build complete context
        self.send_message(sender_id, "I want a perfume")
        time.sleep(1)
        self.send_message(sender_id, "Tell me about Wild Stone perfume")
        time.sleep(1)
        self.send_message(sender_id, "How much does it cost?")
        time.sleep(1)
        
        # Test explicit purchase confirmation
        print(f"\n{Colors.OKCYAN}👤 Customer: Yes, I want to buy the Wild Stone perfume{Colors.ENDC}")
        response = self.send_message(sender_id, "Yes, I want to buy the Wild Stone perfume")
        
        if response:
            print(f"🤖 Agent: {response.get('response_text', 'No response')[:200]}...")
            
            # Should now be ready
            is_ready = response.get('is_ready', False)
            self.log_test("Purchase Confirmation Readiness", is_ready, f"is_ready={is_ready} (should be True)")
            
            # Verify handover data
            product_data = self.verify_product_data(response)
            self.log_test("Handover Product Data", product_data["product_interested"] and product_data["product_ids"],
                         "Both product names and IDs provided for handover")

    def test_multiple_products_workflow(self):
        """Test multiple products handling"""
        self.print_section("MULTIPLE PRODUCTS WORKFLOW")
        
        sender_id = "e2e_test_multiple"
        self.clear_conversation(sender_id)
        
        # Test multiple product interest
        print(f"\n{Colors.OKCYAN}👤 Customer: I need perfume and shampoo{Colors.ENDC}")
        response = self.send_message(sender_id, "I need perfume and shampoo")
        
        if response:
            print(f"🤖 Agent: {response.get('response_text', 'No response')[:150]}...")
            
            # Check if multiple categories are detected
            product_interested = response.get('product_interested', '')
            multiple_detected = ',' in product_interested or 'multiple' in product_interested.lower()
            self.log_test("Multiple Products Detection", multiple_detected,
                         f"product_interested: {product_interested}")

        time.sleep(2)

        # Test specific multiple product selection
        print(f"\n{Colors.OKCYAN}👤 Customer: I'll take the Wild Stone perfume and Garnier shampoo{Colors.ENDC}")
        response = self.send_message(sender_id, "I'll take the Wild Stone perfume and Garnier shampoo")
        
        if response:
            print(f"🤖 Agent: {response.get('response_text', 'No response')[:150]}...")
            
            # Should be ready for multiple products
            is_ready = response.get('is_ready', False)
            self.log_test("Multiple Products Purchase", is_ready, f"is_ready={is_ready} (should be True)")
            
            # Check if multiple product IDs are provided
            product_ids = response.get('interested_product_ids', [])
            multiple_ids = len(product_ids) > 1
            self.log_test("Multiple Product IDs", multiple_ids,
                         f"Product IDs count: {len(product_ids)}")

    def test_conversation_context_retention(self):
        """Test conversation context retention across messages"""
        self.print_section("CONVERSATION CONTEXT RETENTION")
        
        sender_id = "e2e_test_context"
        self.clear_conversation(sender_id)
        
        # Build conversation with context
        self.send_message(sender_id, "I'm looking for a fresh perfume")
        time.sleep(1)
        self.send_message(sender_id, "Something citrusy would be nice")
        time.sleep(1)
        
        # Test context retention
        print(f"\n{Colors.OKCYAN}👤 Customer: Can you remind me what we discussed?{Colors.ENDC}")
        response = self.send_message(sender_id, "Can you remind me what we discussed?")
        
        if response:
            print(f"🤖 Agent: {response.get('response_text', 'No response')[:200]}...")
            
            response_text = response.get('response_text', '').lower()
            context_retained = ('perfume' in response_text and 
                              ('fresh' in response_text or 'citrus' in response_text))
            self.log_test("Conversation Context Retention", context_retained,
                         "Agent referenced previous conversation context")

    def test_edge_cases(self):
        """Test edge cases and error handling"""
        self.print_section("EDGE CASES AND ERROR HANDLING")
        
        # Test 1: Empty message
        sender_id = "e2e_test_edge1"
        self.clear_conversation(sender_id)
        response = self.send_message(sender_id, "")
        
        if response:
            has_response = bool(response.get('response_text'))
            self.log_test("Empty Message Handling", has_response, "Agent handled empty message gracefully")
        else:
            self.log_test("Empty Message Handling", False, "No response to empty message")

        # Test 2: Very long message
        sender_id = "e2e_test_edge2"
        self.clear_conversation(sender_id)
        long_message = "I want perfume " * 100  # Very long message
        response = self.send_message(sender_id, long_message)
        
        if response:
            has_response = bool(response.get('response_text'))
            self.log_test("Long Message Handling", has_response, "Agent handled very long message")

        # Test 3: Special characters
        sender_id = "e2e_test_edge3"
        self.clear_conversation(sender_id)
        response = self.send_message(sender_id, "I want perfume with émoji 🌸 and special chars @#$%")
        
        if response:
            has_response = bool(response.get('response_text'))
            self.log_test("Special Characters Handling", has_response, "Agent handled special characters")

    def run_stress_test(self):
        """Run a stress test with multiple concurrent conversations"""
        self.print_section("STRESS TEST")
        
        import threading
        import concurrent.futures
        
        def single_conversation(conversation_id: int):
            sender_id = f"stress_test_{conversation_id}"
            self.clear_conversation(sender_id)
            
            messages = [
                "I want a perfume",
                "Tell me about Wild Stone",
                "How much does it cost?",
                "I'll buy it"
            ]
            
            for message in messages:
                response = self.send_message(sender_id, message)
                if not response:
                    return False
                time.sleep(0.5)
            
            return True
        
        # Run 5 concurrent conversations
        success_count = 0
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(single_conversation, i) for i in range(5)]
            for future in concurrent.futures.as_completed(futures):
                if future.result():
                    success_count += 1
        
        self.log_test("Concurrent Conversations", success_count == 5, 
                     f"{success_count}/5 conversations completed successfully")

    def print_final_report(self):
        """Print final test report"""
        self.print_header("FINAL TEST REPORT")
        
        total = self.test_results["total_tests"]
        passed = self.test_results["passed"]
        failed = self.test_results["failed"]
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"\n{Colors.BOLD}📊 TEST SUMMARY{Colors.ENDC}")
        print(f"Total Tests: {total}")
        print(f"{Colors.OKGREEN}Passed: {passed}{Colors.ENDC}")
        print(f"{Colors.FAIL}Failed: {failed}{Colors.ENDC}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if self.test_results["errors"]:
            print(f"\n{Colors.FAIL}{Colors.BOLD}❌ FAILED TESTS:{Colors.ENDC}")
            for error in self.test_results["errors"]:
                print(f"   {Colors.FAIL}• {error}{Colors.ENDC}")
        
        if success_rate >= 90:
            print(f"\n{Colors.OKGREEN}{Colors.BOLD}🎉 EXCELLENT! System is working well{Colors.ENDC}")
        elif success_rate >= 75:
            print(f"\n{Colors.WARNING}{Colors.BOLD}⚠️  GOOD, but some issues need attention{Colors.ENDC}")
        else:
            print(f"\n{Colors.FAIL}{Colors.BOLD}🚨 CRITICAL ISSUES detected - system needs fixes{Colors.ENDC}")

    def run_all_tests(self):
        """Run all end-to-end tests"""
        self.print_header("SALES AGENT MICROSERVICE - END-TO-END TESTING")
        print(f"{Colors.OKCYAN}Testing complete workflow from customer inquiry to purchase readiness{Colors.ENDC}")
        print(f"{Colors.OKCYAN}Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.ENDC}")
        
        # Connect to databases
        self.connect_databases()
        
        # Test API health
        self.test_api_health()
        
        # Run workflow tests
        self.test_product_discovery_workflow()
        self.test_price_inquiry_workflow()
        self.test_purchase_confirmation_workflow()
        self.test_multiple_products_workflow()
        self.test_conversation_context_retention()
        
        # Test edge cases
        self.test_edge_cases()
        
        # Run stress test
        self.run_stress_test()
        
        # Print final report
        self.print_final_report()
        
        # Cleanup
        if self.postgres_conn:
            self.postgres_conn.close()
        if self.mongo_client:
            self.mongo_client.close()

def main():
    """Main function"""
    print(f"{Colors.HEADER}🚀 Starting Master End-to-End Testing{Colors.ENDC}")
    print(f"{Colors.OKCYAN}Make sure the following services are running:{Colors.ENDC}")
    print(f"{Colors.OKCYAN}  • Sales Agent API (port 8000){Colors.ENDC}")
    print(f"{Colors.OKCYAN}  • PostgreSQL (port 5432){Colors.ENDC}")
    print(f"{Colors.OKCYAN}  • MongoDB (port 27017){Colors.ENDC}")
    
    # Wait for user confirmation
    input(f"\n{Colors.WARNING}Press Enter to continue once all services are running...{Colors.ENDC}")
    
    # Run tests
    runner = E2ETestRunner()
    runner.run_all_tests()

if __name__ == "__main__":
    main()
