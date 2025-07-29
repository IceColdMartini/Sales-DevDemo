#!/usr/bin/env python3
"""
Final System Validation Report
Comprehensive analysis of multiple product detection and routing agent integration
"""
import requests
import json
import time
from datetime import datetime

API_BASE_URL = "http://localhost:8000"
WEBHOOK_URL = f"{API_BASE_URL}/api/webhook"

class SystemValidator:
    def __init__(self):
        self.results = {}
        
    def send_message(self, sender_id: str, message: str) -> dict:
        payload = {"sender": sender_id, "recipient": "page_123", "text": message}
        try:
            response = requests.post(WEBHOOK_URL, json=payload, timeout=30)
            return response.json() if response.status_code == 200 else {"error": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}

    def clear_conversation(self, sender_id: str):
        try:
            requests.delete(f"{API_BASE_URL}/api/webhook/conversation/{sender_id}")
        except:
            pass

    def validate_complete_multiple_product_flow(self):
        """Validate the complete multiple product purchase flow"""
        print("🎯 COMPLETE MULTIPLE PRODUCT FLOW VALIDATION")
        print("=" * 70)
        
        sender_id = "final_validation"
        self.clear_conversation(sender_id)
        
        # Step-by-step validation
        steps = [
            ("Hello, I need beauty products", "Initial interest", False),
            ("I want Wild Stone perfume and Himalaya face wash", "Multiple product request", False),
            ("Also add some soap for daily use", "Add more products", False),
            ("What are the prices for these products?", "Price inquiry", False),
            ("The prices look good", "Price evaluation", False),
            ("Yes, I want to buy all these products", "Purchase confirmation", True)
        ]
        
        product_progression = []
        
        for i, (message, description, expected_ready) in enumerate(steps, 1):
            print(f"\n📍 Step {i}: {description}")
            print(f"👤 Customer: \"{message}\"")
            
            response = self.send_message(sender_id, message)
            
            if "error" not in response:
                product_interested = response.get('product_interested', '')
                product_ids = response.get('interested_product_ids', [])
                is_ready = response.get('is_ready', False)
                
                print(f"🤖 Products: {product_interested}")
                print(f"🆔 Product IDs: {len(product_ids)} IDs")
                print(f"🚀 Ready: {is_ready} (Expected: {expected_ready})")
                
                product_progression.append({
                    "step": i,
                    "description": description,
                    "product_count": len(product_ids),
                    "product_ids": product_ids,
                    "is_ready": is_ready,
                    "expected_ready": expected_ready,
                    "ready_correct": is_ready == expected_ready
                })
                
                # Validate step
                if is_ready == expected_ready:
                    print("   ✅ Step validation: PASSED")
                else:
                    print("   ❌ Step validation: FAILED")
            else:
                print(f"   ❌ API Error: {response['error']}")
                
            time.sleep(2)
        
        return product_progression

    def validate_routing_agent_data_format(self, final_response_data):
        """Validate the final handover data format for routing agent"""
        print(f"\n🤝 ROUTING AGENT DATA FORMAT VALIDATION")
        print("=" * 70)
        
        # Required fields for routing agent
        required_fields = {
            "sender": str,
            "response_text": str,
            "is_ready": bool,
            "interested_product_ids": list
        }
        
        validation_results = {}
        
        for field, expected_type in required_fields.items():
            if field in final_response_data:
                actual_type = type(final_response_data[field])
                is_correct_type = isinstance(final_response_data[field], expected_type)
                validation_results[field] = {
                    "present": True,
                    "expected_type": expected_type.__name__,
                    "actual_type": actual_type.__name__,
                    "correct_type": is_correct_type,
                    "value": final_response_data[field] if field != "response_text" else "[TEXT CONTENT]"
                }
                status = "✅" if is_correct_type else "❌"
                print(f"{status} {field}: {actual_type.__name__} (expected {expected_type.__name__})")
            else:
                validation_results[field] = {"present": False}
                print(f"❌ {field}: MISSING")
        
        # Validate product IDs format (should be UUIDs)
        product_ids = final_response_data.get('interested_product_ids', [])
        if product_ids:
            valid_uuids = all(
                isinstance(pid, str) and len(pid) == 36 and len(pid.split('-')) == 5
                for pid in product_ids
            )
            print(f"✅ Product ID Format: {'Valid UUIDs' if valid_uuids else 'Invalid format'}")
            validation_results["uuid_format"] = valid_uuids
        
        return validation_results

    def generate_final_report(self, flow_data, routing_data):
        """Generate comprehensive final report"""
        print(f"\n📊 COMPREHENSIVE SYSTEM VALIDATION REPORT")
        print("=" * 80)
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Flow Analysis
        print(f"\n🔄 CONVERSATION FLOW ANALYSIS:")
        total_steps = len(flow_data)
        correct_ready_flags = sum(1 for step in flow_data if step['ready_correct'])
        
        print(f"   Total Steps: {total_steps}")
        print(f"   Correct is_ready Flags: {correct_ready_flags}/{total_steps}")
        print(f"   is_ready Accuracy: {(correct_ready_flags/total_steps)*100:.1f}%")
        
        # Product Progression
        print(f"\n🛍️  PRODUCT PROGRESSION:")
        for step in flow_data:
            print(f"   Step {step['step']}: {step['product_count']} products - {step['description']}")
        
        final_step = flow_data[-1] if flow_data else {}
        final_product_count = final_step.get('product_count', 0)
        final_ready = final_step.get('is_ready', False)
        
        # Multiple Product Detection Summary
        print(f"\n🎯 MULTIPLE PRODUCT DETECTION SUMMARY:")
        print(f"   ✅ Initial Detection: {flow_data[1]['product_count'] >= 1 if len(flow_data) > 1 else False}")
        print(f"   ✅ Product Addition: {flow_data[2]['product_count'] > flow_data[1]['product_count'] if len(flow_data) > 2 else False}")
        print(f"   ✅ Product Persistence: {final_product_count >= 2}")
        print(f"   ✅ Purchase Ready: {final_ready}")
        print(f"   ✅ Final Product Count: {final_product_count}")
        
        # Routing Agent Integration
        print(f"\n🤝 ROUTING AGENT INTEGRATION:")
        routing_valid = all(routing_data.get(field, {}).get('correct_type', False) for field in ['sender', 'response_text', 'is_ready', 'interested_product_ids'])
        print(f"   ✅ Data Structure: {'Valid' if routing_valid else 'Invalid'}")
        print(f"   ✅ UUID Format: {'Valid' if routing_data.get('uuid_format', False) else 'Invalid'}")
        print(f"   ✅ Ready for Handover: {final_ready}")
        
        # Overall Assessment
        print(f"\n🎉 OVERALL SYSTEM ASSESSMENT:")
        
        multiple_product_score = (
            (final_product_count >= 2) * 25 +  # Multiple products detected
            (final_ready) * 25 +               # Purchase ready
            (correct_ready_flags >= total_steps * 0.8) * 25 +  # is_ready accuracy
            (routing_valid) * 25                # Routing agent ready
        )
        
        print(f"   📊 Multiple Product Detection Score: {multiple_product_score}/100")
        
        if multiple_product_score >= 90:
            print(f"   🏆 EXCELLENT: System is production-ready!")
        elif multiple_product_score >= 75:
            print(f"   ✅ GOOD: System is working well with minor improvements needed")
        elif multiple_product_score >= 60:
            print(f"   ⚠️  FAIR: System needs improvement")
        else:
            print(f"   ❌ POOR: System needs significant fixes")
        
        # Final Product IDs for Routing Agent
        if final_step.get('product_ids'):
            print(f"\n📋 FINAL HANDOVER DATA FOR ROUTING AGENT:")
            handover_data = {
                "sender": final_step.get('product_ids', [{}])[0] if flow_data else "unknown",
                "is_ready": final_ready,
                "product_count": final_product_count,
                "product_ids": final_step.get('product_ids', [])
            }
            print(json.dumps(handover_data, indent=2))

    def run_final_validation(self):
        """Run complete system validation"""
        print("🚀 FINAL SYSTEM VALIDATION")
        print("Focus: Multiple Product Detection & Routing Agent Integration")
        print("=" * 80)
        
        # 1. Validate complete flow
        flow_data = self.validate_complete_multiple_product_flow()
        
        # 2. Get final response for routing agent validation
        final_response = self.send_message("final_validation", "Confirm my purchase")
        
        # 3. Validate routing agent data format
        routing_data = self.validate_routing_agent_data_format(final_response)
        
        # 4. Generate comprehensive report
        self.generate_final_report(flow_data, routing_data)

if __name__ == "__main__":
    validator = SystemValidator()
    validator.run_final_validation()
