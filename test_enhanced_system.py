#!/usr/bin/env python3
"""
Test the Enhanced Conversation System
Tests the specific improvements made to fix identified issues
"""

import requests
import json
import time
from typing import Dict

# API Configuration
API_BASE_URL = "http://localhost:8000"
WEBHOOK_URL = f"{API_BASE_URL}/api/webhook"

class EnhancedSystemTester:
    def __init__(self):
        self.test_results = []
        
    def log_test_result(self, test_name: str, passed: bool, details: str = ""):
        """Log test results for final summary"""
        self.test_results.append({
            "test": test_name,
            "passed": passed,
            "details": details
        })
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status} - {test_name}")
        if details:
            print(f"    Details: {details}")
        
    def send_message(self, sender_id: str, message: str) -> Dict:
        """Send a message to the sales agent"""
        payload = {
            "sender": sender_id,
            "recipient": "page_123",
            "text": message
        }
        
        try:
            response = requests.post(WEBHOOK_URL, json=payload, timeout=30)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ API Error {response.status_code}: {response.text}")
                return None
        except Exception as e:
            print(f"❌ Request Error: {e}")
            return None

    def clear_conversation(self, sender_id: str):
        """Clear conversation history for a user"""
        try:
            response = requests.delete(f"{API_BASE_URL}/api/webhook/conversation/{sender_id}")
            print(f"🧹 Cleared conversation for {sender_id}")
        except Exception as e:
            print(f"⚠️ Warning: Could not clear conversation for {sender_id}: {e}")

    def test_fixed_conversation_continuity(self):
        """Test that conversation continuity is now maintained properly"""
        print("\n🔧 TESTING FIXED CONVERSATION CONTINUITY")
        print("=" * 60)
        
        sender_id = "test_fixed_continuity"
        self.clear_conversation(sender_id)
        
        # Build conversation context
        messages = [
            "I need a good perfume",
            "Tell me about Wild Stone",
            "What are the benefits?",
            "How much does it cost?",
            "That sounds good"
        ]
        
        continuity_maintained = True
        
        for i, message in enumerate(messages, 1):
            print(f"\n📝 Step {i}: '{message}'")
            print("-" * 40)
            
            response = self.send_message(sender_id, message)
            if not response:
                continuity_maintained = False
                continue
                
            response_text = response.get('response_text', '').lower()
            
            # Check if Wild Stone perfume context is maintained
            maintains_context = (
                'wild stone' in response_text or 
                'perfume' in response_text or
                response.get('product_interested', '').lower() in ['wild stone', 'wild stone perfume']
            )
            
            print(f"🤖 Response: {response['response_text'][:100]}...")
            print(f"🛍️ Product Interest: {response.get('product_interested', 'None')}")
            print(f"✅ Maintains Context: {maintains_context}")
            
            if not maintains_context and i > 1:  # Allow first message to not have specific context
                continuity_maintained = False
                
            time.sleep(1)
        
        self.log_test_result("Fixed Conversation Continuity", continuity_maintained)

    def test_fixed_purchase_confirmation_flow(self):
        """Test that purchase confirmation now works properly"""
        print("\n🔧 TESTING FIXED PURCHASE CONFIRMATION FLOW")
        print("=" * 60)
        
        sender_id = "test_fixed_purchase_flow"
        self.clear_conversation(sender_id)
        
        # Proper purchase flow
        flow_steps = [
            {"message": "I need Wild Stone perfume", "should_be_ready": False},
            {"message": "How much does it cost?", "should_be_ready": False},
            {"message": "I'm interested in buying it", "should_be_ready": False},  # Should ask for confirmation
            {"message": "Yes, I want to buy the Wild Stone perfume", "should_be_ready": True}  # Explicit confirmation
        ]
        
        all_stages_correct = True
        
        for i, step in enumerate(flow_steps, 1):
            print(f"\n📝 Stage {i}: '{step['message']}'")
            print(f"🎯 Expected is_ready: {step['should_be_ready']}")
            print("-" * 50)
            
            response = self.send_message(sender_id, step['message'])
            if not response:
                all_stages_correct = False
                continue
                
            actual_ready = response.get('is_ready', False)
            expected_ready = step['should_be_ready']
            
            print(f"🤖 Response: {response['response_text'][:80]}...")
            print(f"🚀 Actual is_ready: {actual_ready}")
            print(f"✅ Expected Match: {actual_ready == expected_ready}")
            
            if actual_ready != expected_ready:
                all_stages_correct = False
                
            time.sleep(1)
        
        self.log_test_result("Fixed Purchase Confirmation Flow", all_stages_correct)

    def test_fixed_multiple_products_handling(self):
        """Test that multiple products are now handled correctly"""
        print("\n🔧 TESTING FIXED MULTIPLE PRODUCTS HANDLING")
        print("=" * 60)
        
        sender_id = "test_fixed_multiple_products"
        self.clear_conversation(sender_id)
        
        # Multiple products flow
        print("\n📝 Step 1: Request multiple products")
        print("-" * 40)
        
        response = self.send_message(sender_id, "I want Wild Stone perfume and Himalaya shampoo")
        multiple_products_mentioned = False
        
        if response:
            print(f"🤖 Response: {response['response_text'][:100]}...")
            print(f"🛍️ Product Interest: {response.get('product_interested', 'None')}")
            print(f"🆔 Product IDs: {response.get('interested_product_ids', [])}")
            
            product_interest = response.get('product_interested', '').lower()
            multiple_products_mentioned = (
                'multiple products' in product_interest or
                len(response.get('interested_product_ids', [])) > 1 or
                ('wild stone' in product_interest and 'shampoo' in product_interest)
            )
            
            print(f"🔍 Multiple Products Detected: {multiple_products_mentioned}")
        
        time.sleep(2)
        
        # Purchase confirmation for multiple products
        print("\n📝 Step 2: Purchase confirmation")
        print("-" * 40)
        
        response = self.send_message(sender_id, "Yes, I want to buy both of them")
        
        if response:
            print(f"🤖 Response: {response['response_text']}")
            print(f"🚀 Is Ready: {response.get('is_ready', False)}")
            print(f"🛍️ Product Interest: {response.get('product_interested', 'None')}")
            print(f"🆔 Product IDs: {response.get('interested_product_ids', [])}")
            
            multiple_products_handled = (
                response.get('is_ready', False) and
                ('multiple' in response.get('product_interested', '').lower() or
                 len(response.get('interested_product_ids', [])) > 1)
            )
            
            self.log_test_result("Fixed Multiple Products Handling", multiple_products_handled)
        else:
            self.log_test_result("Fixed Multiple Products Handling", False, "No response")

    def test_fixed_product_removal(self):
        """Test that product removal now works correctly"""
        print("\n🔧 TESTING FIXED PRODUCT REMOVAL")
        print("=" * 60)
        
        sender_id = "test_fixed_product_removal"
        self.clear_conversation(sender_id)
        
        # Build up multiple product selection
        setup_messages = [
            "I need perfume and shampoo",
            "Show me Wild Stone perfume and Himalaya shampoo"
        ]
        
        print("🔧 Setting up product selection...")
        for msg in setup_messages:
            response = self.send_message(sender_id, msg)
            time.sleep(1)
        
        # Remove one product
        print("\n📝 Step 1: Remove shampoo")
        print("-" * 40)
        
        response = self.send_message(sender_id, "Actually, I don't want the shampoo")
        removal_handled = False
        
        if response:
            print(f"🤖 Response: {response['response_text']}")
            print(f"🛍️ Product Interest: {response.get('product_interested', 'None')}")
            
            product_interest = response.get('product_interested', '').lower()
            perfume_remains = 'perfume' in product_interest or 'wild stone' in product_interest
            shampoo_removed = 'shampoo' not in product_interest
            
            print(f"🌟 Perfume Remains: {perfume_remains}")
            print(f"🚫 Shampoo Removed: {shampoo_removed}")
            
            removal_handled = perfume_remains and shampoo_removed
        
        time.sleep(2)
        
        # Confirm remaining product
        print("\n📝 Step 2: Confirm remaining product")
        print("-" * 40)
        
        response = self.send_message(sender_id, "Yes, I'll take just the perfume")
        
        if response:
            print(f"🚀 Is Ready: {response.get('is_ready', False)}")
            print(f"🛍️ Product Interest: {response.get('product_interested', 'None')}")
            
            final_success = (
                response.get('is_ready', False) and
                removal_handled
            )
            
            self.log_test_result("Fixed Product Removal", final_success)
        else:
            self.log_test_result("Fixed Product Removal", False, "No final response")

    def test_enhanced_conversation_summary(self):
        """Test that conversation summary now works properly"""
        print("\n🔧 TESTING ENHANCED CONVERSATION SUMMARY")
        print("=" * 60)
        
        sender_id = "test_enhanced_summary"
        self.clear_conversation(sender_id)
        
        # Build conversation context
        context_messages = [
            "Hi, I want a good perfume",
            "Tell me about Wild Stone perfume",
            "How much does it cost?"
        ]
        
        print("🔧 Building conversation context...")
        for msg in context_messages:
            response = self.send_message(sender_id, msg)
            time.sleep(1)
        
        # Ask for conversation summary
        print("\n📝 Asking for conversation summary")
        print("-" * 40)
        
        response = self.send_message(sender_id, "Tell me what our current conversation is about")
        
        if response:
            print(f"🤖 Response: {response['response_text']}")
            
            response_text = response.get('response_text', '').lower()
            
            # Check if summary references actual conversation
            references_perfume = 'perfume' in response_text
            references_wild_stone = 'wild stone' in response_text
            references_price = any(word in response_text for word in ['price', 'cost', '₹'])
            not_generic = not ('all our products' in response_text or 'wide range' in response_text)
            
            print(f"✅ References Perfume: {references_perfume}")
            print(f"✅ References Wild Stone: {references_wild_stone}")
            print(f"✅ References Price Discussion: {references_price}")
            print(f"✅ Not Generic Response: {not_generic}")
            
            summary_improved = references_perfume and not_generic
            
            self.log_test_result("Enhanced Conversation Summary", summary_improved)
        else:
            self.log_test_result("Enhanced Conversation Summary", False, "No response")

    def run_enhanced_tests(self):
        """Run all enhanced system tests"""
        print("🚀 TESTING ENHANCED CONVERSATION SYSTEM")
        print("=" * 80)
        print("Testing fixes for identified issues in the conversation flow")
        print("=" * 80)
        
        # Run all enhanced tests
        self.test_fixed_conversation_continuity()
        self.test_fixed_purchase_confirmation_flow()
        self.test_fixed_multiple_products_handling()
        self.test_fixed_product_removal()
        self.test_enhanced_conversation_summary()
        
        # Print summary
        self.print_enhanced_test_summary()

    def print_enhanced_test_summary(self):
        """Print summary of enhanced system tests"""
        print("\n" + "="*80)
        print("📊 ENHANCED SYSTEM TEST SUMMARY")
        print("="*80)
        
        passed_tests = sum(1 for result in self.test_results if result['passed'])
        total_tests = len(self.test_results)
        
        print(f"\n🎯 Enhanced System Score: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            print("🎉 ALL ENHANCED TESTS PASSED! System improvements are working correctly.")
        elif passed_tests > total_tests * 0.7:
            print("✅ GOOD: Most improvements are working correctly.")
        else:
            print("⚠️ NEEDS WORK: Some enhancements still need fixes.")
            
        print(f"\n📈 Improvement Rate: {(passed_tests/total_tests)*100:.1f}%")

if __name__ == "__main__":
    tester = EnhancedSystemTester()
    tester.run_enhanced_tests()
