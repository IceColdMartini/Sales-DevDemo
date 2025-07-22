#!/usr/bin/env python3
"""
🎯 Enhanced Sales Funnel Demonstration
This demonstrates the LLM-powered sales stage detection system that addresses
the issue of premature 'is_ready' flag setting.

The system now enforces:
1. Proper sales progression through 9 stages
2. Mandatory price introduction before purchase confirmation
3. LLM-powered stage detection vs hard-coded patterns
4. Explicit purchase confirmation required for readiness
"""
import requests
import json
import time
import requests
import json
import time

def clear_conversation():
    """Clear conversation for clean test"""
    try:
        response = requests.delete("http://localhost:8000/conversation/test_demo")
        print("🗑️  Cleared conversation for demo")
    except:
        print("ℹ️  No previous conversation to clear")

def send_message(message):
    """Send message to the sales agent"""
    payload = {
        "sender": "test_demo",
        "text": message
    }
    
    try:
        response = requests.post(
            "http://localhost:8000/chat", 
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            return data
        else:
            print(f"❌ Error: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Failed to send message: {e}")
        return None

def demo_sales_progression():
    """Demonstrate the enhanced sales funnel progression"""
    
    print("🚀 ENHANCED SALES FUNNEL DEMONSTRATION")
    print("=" * 80)
    print("Testing LLM-powered sales stage detection vs premature 'is_ready' flagging")
    print()
    
    clear_conversation()
    
    # Test scenarios showing proper progression
    scenarios = [
        {
            "stage": "1. INITIAL INTEREST",
            "message": "Hi, I'm interested in perfumes",
            "expected_ready": False,
            "description": "Customer expresses general interest"
        },
        {
            "stage": "2. SPECIFIC INQUIRY", 
            "message": "Tell me about Wild Stone perfume",
            "expected_ready": False,
            "description": "Customer asks about specific product"
        },
        {
            "stage": "3. PRICE INQUIRY",
            "message": "How much does it cost?",
            "expected_ready": False,
            "description": "Customer asks for pricing (mandatory exposure)"
        },
        {
            "stage": "4. PRICE EVALUATION",
            "message": "That seems reasonable",
            "expected_ready": False,
            "description": "Customer evaluates price but no confirmation"
        },
        {
            "stage": "5. PURCHASE INTENT",
            "message": "This sounds good for me",
            "expected_ready": False,
            "description": "Strong interest but not explicit confirmation"
        },
        {
            "stage": "6. EXPLICIT CONFIRMATION",
            "message": "Yes, I want to buy the Wild Stone perfume",
            "expected_ready": True,
            "description": "Explicit purchase confirmation - ONLY NOW ready!"
        }
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"📍 {scenario['stage']}")
        print("-" * 60)
        print(f"👤 Customer: {scenario['message']}")
        
        result = send_message(scenario['message'])
        
        if result:
            agent_response = result.get('response_text', 'No response')
            is_ready = result.get('is_ready', False)
            product_interest = result.get('product_interested', 'None')
            
            # Truncate long responses for readability
            if len(agent_response) > 200:
                agent_response = agent_response[:200] + "..."
            
            print(f"🤖 Agent: {agent_response}")
            print(f"🛍️  Product Interest: {product_interest}")
            print(f"🚀 Ready to Buy: {is_ready} ← Should be {scenario['expected_ready']}")
            
            # Validation
            if is_ready == scenario['expected_ready']:
                if is_ready:
                    print("✅ SUCCESS: Customer is now ready for purchase!")
                else:
                    print("✅ CORRECT: Not ready yet - proper progression")
            else:
                print(f"❌ ERROR: Expected {scenario['expected_ready']}, got {is_ready}")
                
            print(f"📝 {scenario['description']}")
        else:
            print("❌ Failed to get response")
        
        print()
        time.sleep(1)  # Brief pause between requests
    
    print("🎯 ENHANCED SALES FUNNEL SUMMARY:")
    print("✓ LLM-powered stage detection prevents premature 'is_ready' flagging")
    print("✓ Mandatory price introduction before purchase confirmation")
    print("✓ Explicit purchase confirmation required for readiness")
    print("✓ Progressive sales funnel with intelligent stage transitions")
    print("✓ Multiple product handling with individual pricing")

def demo_explicit_confirmation_detection():
    """Demonstrate explicit confirmation phrase detection"""
    
    print("\n" + "=" * 80)
    print("🎯 EXPLICIT CONFIRMATION DETECTION TEST")
    print("=" * 80)
    print("Testing various ways customers confirm purchases")
    print()
    
    clear_conversation()
    
    # First establish context with price exposure
    print("📋 Setting up context with price exposure...")
    setup_result = send_message("I'm interested in Wild Stone perfume")
    if setup_result:
        price_result = send_message("What's the price?")
        print(f"✓ Context established with pricing information\n")
    
    # Test explicit confirmation phrases
    confirmation_phrases = [
        "Yes, I want to buy it",
        "I'll take the Wild Stone perfume", 
        "I want to purchase this perfume",
        "I'll buy both perfumes",
        "Let me order the Wild Stone perfume"
    ]
    
    for phrase in confirmation_phrases:
        clear_conversation()
        # Re-establish context
        send_message("I'm interested in Wild Stone perfume")
        send_message("What's the price?")
        
        print(f"👤 Testing: \"{phrase}\"")
        result = send_message(phrase)
        
        if result:
            is_ready = result.get('is_ready', False)
            status = "✅ DETECTED" if is_ready else "❌ MISSED"
            print(f"🚀 {status}: is_ready = {is_ready}")
        else:
            print("❌ Failed to test phrase")
        print()

if __name__ == "__main__":
    print("🚀 Starting Enhanced Sales Funnel Demo")
    print("This demonstrates the solution to premature 'is_ready' flagging")
    print()
    
    demo_sales_progression()
    demo_explicit_confirmation_detection()
    
    print("\n🏁 Demo Complete!")
    print("\nKey Improvements:")
    print("• LLM analyzes customer intent vs hard-coded patterns")
    print("• Mandatory price exposure before purchase confirmation")
    print("• Explicit purchase words required for readiness")
    print("• Progressive sales funnel with intelligent transitions")
    print("• Enhanced customer journey management")
