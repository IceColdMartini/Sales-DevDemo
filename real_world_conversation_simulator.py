"""
Real-World Conversation Simulator
=================================

Interactive simulator for testing the enhanced conversation system with realistic scenarios.
This script allows you to experience the conversation system as a real customer would.
"""

import asyncio
import json
import logging
import sys
import time
from datetime import datetime
from typing import Dict, List, Any
from fastapi.testclient import TestClient

# Configure logging for better visibility
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add the project root to Python path
sys.path.append('/Users/Kazi/Desktop/Sales-DevDemo')

from main import app
from app.models.schemas import Message
from app.db.mongo_handler import mongo_handler
from app.db.postgres_handler import postgres_handler

class RealWorldConversationSimulator:
    """
    Interactive real-world conversation simulator for testing the enhanced system.
    """

    def __init__(self):
        self.client = TestClient(app)
        self.session_id = f"realworld_{int(time.time())}"
        
        # Realistic customer personas with backstories
        self.customer_personas = {
            "busy_mom": {
                "name": "Sarah (Busy Mom)",
                "backstory": "Working mom of 2, limited time, wants effective products",
                "conversation_style": "Direct, efficient, mentions time constraints",
                "budget_range": "$30-80",
                "skin_concerns": ["dry skin", "dark circles", "quick routine"]
            },
            "skincare_enthusiast": {
                "name": "Emma (Skincare Enthusiast)", 
                "backstory": "22-year-old college student, loves trying new products",
                "conversation_style": "Detailed questions, mentions ingredients and reviews",
                "budget_range": "$15-50",
                "skin_concerns": ["acne", "blackheads", "oily t-zone", "sensitive skin"]
            },
            "gift_shopper": {
                "name": "Michael (Gift Shopper)",
                "backstory": "Buying anniversary gift for wife, uncertain about products",
                "conversation_style": "Asks lots of questions, mentions recipient",
                "budget_range": "$50-150",
                "skin_concerns": ["anti-aging", "luxury feel", "gift presentation"]
            },
            "budget_conscious": {
                "name": "Alex (Budget-Conscious)",
                "backstory": "Recent graduate, tight budget, wants value for money",
                "conversation_style": "Price-focused, asks about deals and alternatives",
                "budget_range": "$10-40",
                "skin_concerns": ["basic skincare", "affordable", "multi-purpose"]
            },
            "first_time_buyer": {
                "name": "Jennifer (First-Time Buyer)",
                "backstory": "Never bought skincare online, cautious about trying new products",
                "conversation_style": "Hesitant, asks about guarantees and returns",
                "budget_range": "$20-60",
                "skin_concerns": ["gentle products", "sensitive skin", "beginner-friendly"]
            }
        }

        # Realistic conversation scenarios
        self.conversation_scenarios = {
            "morning_routine": [
                "Hi! I'm looking to upgrade my morning skincare routine. I have combination skin and work long hours, so I need something effective but quick.",
                "That sounds good. Can you tell me more about the ingredients? I've heard good things about vitamin C serums.",
                "I like that it's gentle. What about moisturizers? I need something that works well under makeup.",
                "Perfect! What would be the total cost for the serum and moisturizer? Is there any bundle discount?",
                "Great! I'd like to get both products. How do I place the order?"
            ],
            "acne_solution": [
                "I'm struggling with adult acne and it's really affecting my confidence. Can you help me find something that actually works?",
                "I've tried so many products before and they either don't work or irritate my skin. What makes your products different?",
                "That's exactly what I need! I'm tired of harsh treatments. Can you recommend a complete routine?",
                "This sounds promising. I'm willing to invest in good products. What's the price for the full routine?",
                "You've convinced me! I really need to see results. Please help me order this routine."
            ],
            "gift_shopping": [
                "Hi! I need help finding the perfect skincare gift for my girlfriend. She's turning 28 and loves taking care of her skin.",
                "She has normal to dry skin and she's mentioned wanting to start anti-aging prevention. What would you recommend?",
                "That sounds perfect for her! I want to get something really special. What would be a nice gift set in the $100-120 range?",
                "Excellent! She's going to love this. Can you help me with gift wrapping and delivery options?",
                "Perfect! I'll take the luxury gift set. This will make her so happy!"
            ],
            "budget_shopping": [
                "I'm new to skincare and on a student budget. I need basic products that won't break the bank but actually work.",
                "That's helpful! I can spend maybe $35-40 total. Do you have any starter sets or travel sizes?",
                "Great! I love that there are smaller sizes to try first. Are there any current promotions or student discounts?",
                "Perfect! That fits my budget exactly. I'll take the starter set. Thank you for helping me find something affordable!"
            ],
            "sensitive_skin": [
                "I have extremely sensitive skin that reacts to everything. I'm scared to try new products but I really need help with my skincare.",
                "I've had bad reactions before - redness, burning, breakouts. What ingredients should I avoid? Do you have gentle options?",
                "That's reassuring. I really want to try but I'm nervous. Do you have samples or a return policy if products don't work for me?",
                "Okay, I feel more confident now. I'll start with the gentle cleanser and see how my skin reacts. Can I order just that for now?"
            ]
        }

    async def initialize_system(self):
        """Initialize database connections and system components."""
        try:
            print("🔧 Initializing Real-World Conversation Simulator...")
            
            # Test database connections
            print("📊 Connecting to databases...")
            
            # MongoDB Atlas
            print("  • MongoDB Atlas (Cloud)...")
            try:
                mongo_handler.get_conversation("test_connection")
                print("    ✅ MongoDB Atlas connected")
            except Exception as e:
                print(f"    ❌ MongoDB connection error: {e}")
                
            # PostgreSQL Neon  
            print("  • PostgreSQL Neon...")
            try:
                products = postgres_handler.get_all_products()
                print(f"    ✅ PostgreSQL connected - {len(products)} products available")
            except Exception as e:
                print(f"    ❌ PostgreSQL connection error: {e}")
            
            print("✅ System initialized successfully!")
            
        except Exception as e:
            print(f"❌ System initialization failed: {e}")
            raise

    def display_personas(self):
        """Display available customer personas."""
        print("\n👥 Available Customer Personas:")
        print("=" * 50)
        
        for persona_id, persona in self.customer_personas.items():
            print(f"\n🎭 {persona['name']}")
            print(f"   Background: {persona['backstory']}")
            print(f"   Style: {persona['conversation_style']}")
            print(f"   Budget: {persona['budget_range']}")
            print(f"   Concerns: {', '.join(persona['skin_concerns'])}")

    def display_scenarios(self):
        """Display available conversation scenarios."""
        print("\n💬 Available Conversation Scenarios:")
        print("=" * 50)
        
        scenarios = {
            "morning_routine": "🌅 Morning Routine - Customer wants to upgrade their daily routine",
            "acne_solution": "🔴 Acne Solution - Customer struggling with adult acne",
            "gift_shopping": "🎁 Gift Shopping - Buying products as a gift",
            "budget_shopping": "💰 Budget Shopping - Student looking for affordable options", 
            "sensitive_skin": "🌸 Sensitive Skin - Customer with reactive, sensitive skin"
        }
        
        for scenario_id, description in scenarios.items():
            print(f"\n{description}")

    async def run_interactive_simulation(self):
        """Run an interactive conversation simulation."""
        print("\n🎬 INTERACTIVE CONVERSATION SIMULATION")
        print("=" * 60)
        print("Experience the enhanced conversation system as a real customer!")
        
        # Display options
        self.display_personas()
        self.display_scenarios()
        
        print("\n🎯 Choose your simulation mode:")
        print("1. Select a persona + scenario (guided)")
        print("2. Free-form conversation (manual)")
        print("3. Run all scenarios automatically")
        
        mode = input("\nEnter mode (1-3): ").strip()
        
        if mode == "1":
            await self.run_guided_simulation()
        elif mode == "2":
            await self.run_freeform_simulation()
        elif mode == "3":
            await self.run_all_scenarios()
        else:
            print("❌ Invalid mode selected")

    async def run_guided_simulation(self):
        """Run a guided simulation with selected persona and scenario."""
        print("\n🎭 GUIDED SIMULATION")
        
        # Select persona
        print("\nAvailable personas:", list(self.customer_personas.keys()))
        persona_choice = input("Choose persona: ").strip()
        
        if persona_choice not in self.customer_personas:
            print("❌ Invalid persona")
            return
            
        # Select scenario
        print("\nAvailable scenarios:", list(self.conversation_scenarios.keys()))
        scenario_choice = input("Choose scenario: ").strip()
        
        if scenario_choice not in self.conversation_scenarios:
            print("❌ Invalid scenario")
            return
        
        # Run the simulation
        persona = self.customer_personas[persona_choice]
        scenario = self.conversation_scenarios[scenario_choice]
        
        await self.simulate_conversation(persona, scenario)

    async def run_freeform_simulation(self):
        """Run a free-form conversation where user types their own messages."""
        print("\n💭 FREE-FORM CONVERSATION")
        print("Type your messages as if you're a real customer!")
        print("Type 'quit' to end the conversation\n")
        
        customer_id = f"freeform_{int(time.time())}"
        
        while True:
            user_input = input("👤 You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'bye']:
                break
                
            if not user_input:
                continue
                
            # Send message to system
            response = await self.send_message(customer_id, user_input)
            
            # Display AI response
            print(f"🤖 AI: {response.get('response_text', 'No response')}")
            print(f"📊 Stage: {response.get('conversation_stage', 'Unknown')}")
            
            if response.get('is_ready'):
                print("🎯 Customer is ready to buy!")
                
            if response.get('handover'):
                print("📞 System recommends handover to human agent")
                break
                
            print()

    async def run_all_scenarios(self):
        """Run all predefined scenarios automatically."""
        print("\n🚀 RUNNING ALL SCENARIOS AUTOMATICALLY")
        
        results = []
        
        for persona_name, persona in self.customer_personas.items():
            for scenario_name, scenario in self.conversation_scenarios.items():
                print(f"\n{'='*60}")
                print(f"🎭 Testing: {persona['name']} - {scenario_name}")
                print(f"{'='*60}")
                
                result = await self.simulate_conversation(persona, scenario, auto_mode=True)
                results.append({
                    "persona": persona_name,
                    "scenario": scenario_name,
                    "result": result
                })
                
                # Brief pause between scenarios
                await asyncio.sleep(1)
        
        # Display summary
        self.display_automation_summary(results)

    async def simulate_conversation(self, persona: Dict, scenario: List[str], auto_mode: bool = False) -> Dict:
        """Simulate a complete conversation."""
        
        customer_id = f"sim_{persona['name'].replace(' ', '_')}_{int(time.time())}"
        
        print(f"\n🎭 Customer: {persona['name']}")
        print(f"📖 Background: {persona['backstory']}")
        print(f"💰 Budget: {persona['budget_range']}")
        print(f"🎯 Concerns: {', '.join(persona['skin_concerns'])}")
        print("\n" + "="*50)
        
        conversation_log = []
        total_time = 0
        
        for i, message in enumerate(scenario):
            step_start = time.time()
            
            if not auto_mode:
                input(f"\n👤 Press Enter to send message {i+1}/{len(scenario)}...")
            
            print(f"\n👤 {persona['name']}: {message}")
            
            # Send message to system
            response = await self.send_message(customer_id, message)
            
            step_time = time.time() - step_start
            total_time += step_time
            
            # Display AI response
            ai_response = response.get('response_text', 'No response received')
            print(f"\n🤖 AI Assistant: {ai_response}")
            
            # Display system metrics
            stage = response.get('conversation_stage', 'Unknown')
            confidence = response.get('confidence', 0)
            is_ready = response.get('is_ready', False)
            
            print(f"\n📊 System Metrics:")
            print(f"   Stage: {stage}")
            print(f"   Confidence: {confidence:.2f}")
            print(f"   Ready to Buy: {'Yes' if is_ready else 'No'}")
            print(f"   Response Time: {step_time:.2f}s")
            
            # Log conversation step
            conversation_log.append({
                "step": i + 1,
                "customer_message": message,
                "ai_response": ai_response,
                "stage": stage,
                "confidence": confidence,
                "is_ready": is_ready,
                "response_time": step_time
            })
            
            # Check for handover
            if response.get('handover'):
                print("📞 System recommends handover to human agent")
                break
            
            if not auto_mode and i < len(scenario) - 1:
                print("\n" + "-"*50)
        
        # Conversation summary
        avg_response_time = total_time / len(scenario)
        final_stage = conversation_log[-1]['stage'] if conversation_log else 'Unknown'
        final_ready = conversation_log[-1]['is_ready'] if conversation_log else False
        
        print(f"\n🏁 CONVERSATION SUMMARY:")
        print(f"   Total Steps: {len(conversation_log)}")
        print(f"   Total Time: {total_time:.2f}s")
        print(f"   Average Response Time: {avg_response_time:.2f}s")
        print(f"   Final Stage: {final_stage}")
        print(f"   Purchase Ready: {'Yes' if final_ready else 'No'}")
        
        return {
            "persona": persona['name'],
            "conversation_log": conversation_log,
            "total_time": total_time,
            "avg_response_time": avg_response_time,
            "final_stage": final_stage,
            "purchase_ready": final_ready,
            "success": final_ready and final_stage in ['PURCHASE_INTENT', 'PURCHASE_CONFIRMATION']
        }

    async def send_message(self, customer_id: str, message: str) -> Dict[str, Any]:
        """Send a message to the conversation system."""
        try:
            # Create message payload
            message_data = {
                "sender": customer_id,
                "recipient": "assistant", 
                "text": message
            }
            
            # Send to webhook endpoint
            response = self.client.post("/api/webhook", json=message_data)
            
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "error": f"HTTP {response.status_code}",
                    "response_text": "Sorry, I'm experiencing technical difficulties."
                }
                
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return {
                "error": str(e),
                "response_text": "Sorry, I encountered an error processing your message."
            }

    def display_automation_summary(self, results: List[Dict]):
        """Display summary of automated scenario testing."""
        
        print("\n" + "="*80)
        print("📊 AUTOMATION SUMMARY")
        print("="*80)
        
        total_scenarios = len(results)
        successful_scenarios = sum(1 for r in results if r['result']['success'])
        success_rate = (successful_scenarios / total_scenarios) * 100
        
        print(f"🎯 Total Scenarios Tested: {total_scenarios}")
        print(f"✅ Successful Conversations: {successful_scenarios}")
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        # Average metrics
        avg_time = sum(r['result']['total_time'] for r in results) / total_scenarios
        avg_response_time = sum(r['result']['avg_response_time'] for r in results) / total_scenarios
        
        print(f"⏱️ Average Conversation Time: {avg_time:.2f}s")
        print(f"⚡ Average Response Time: {avg_response_time:.2f}s")
        
        # Stage distribution
        final_stages = [r['result']['final_stage'] for r in results]
        stage_counts = {}
        for stage in final_stages:
            stage_counts[stage] = stage_counts.get(stage, 0) + 1
        
        print(f"\n📊 Final Stage Distribution:")
        for stage, count in stage_counts.items():
            percentage = (count / total_scenarios) * 100
            print(f"   {stage}: {count} ({percentage:.1f}%)")
        
        # Detailed results
        print(f"\n📋 Detailed Results:")
        for result in results:
            persona = result['persona']
            scenario = result['scenario'] 
            success = "✅" if result['result']['success'] else "❌"
            stage = result['result']['final_stage']
            time_taken = result['result']['total_time']
            
            print(f"   {success} {persona} - {scenario}: {stage} ({time_taken:.1f}s)")

async def main():
    """Main function to run the real-world conversation simulator."""
    
    print("🌍 REAL-WORLD CONVERSATION SIMULATOR")
    print("="*60)
    print("Experience the enhanced conversation system with realistic customer interactions!")
    
    simulator = RealWorldConversationSimulator()
    
    try:
        # Initialize system
        await simulator.initialize_system()
        
        # Run simulation
        await simulator.run_interactive_simulation()
        
        print("\n🎉 Simulation completed!")
        
    except KeyboardInterrupt:
        print("\n\n👋 Simulation interrupted by user")
    except Exception as e:
        print(f"\n❌ Simulation failed: {e}")
        logger.error(f"Simulation error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
