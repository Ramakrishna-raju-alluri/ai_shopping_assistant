#!/usr/bin/env python3
"""
Quick test to verify cart functionality
"""

import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_cart_add():
    """Test adding items to cart"""
    print("🛒 Testing Cart Add Functionality...")
    print("=" * 50)
    
    try:
        from agents.grocery_list_agent import GroceryListAgent
        
        agent = GroceryListAgent()
        
        # Test adding eggs
        result = agent.process_message(
            user_message="add eggs to my cart",
            user_id="test_user",
            session_id="test_session"
        )
        
        print(f"Result: {result.get('message', 'No message')[:200]}...")
        
        if "added" in result.get('message', '').lower():
            print("✅ Cart add functionality working!")
        else:
            print("⚠️ Cart add might have issues")
            
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")

if __name__ == "__main__":
    test_cart_add()