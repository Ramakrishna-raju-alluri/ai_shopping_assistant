#!/usr/bin/env python3
"""
Simple test script for the Grocery List Agent
Run this to test the basic functionality locally
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.grocery_list_agent import grocery_list_agent

def test_basic_functionality():
    """Test basic agent functionality"""
    print("🧪 Testing Grocery List Agent...")
    print("=" * 50)
    
    # Test 1: Agent initialization
    try:
        agent = grocery_list_agent.get_agent()
        print("✅ Agent initialization: SUCCESS")
    except Exception as e:
        print(f"❌ Agent initialization: FAILED - {e}")
        return False
    
    # Test 2: Process simple message
    try:
        response = grocery_list_agent.process_message(
            user_message="add eggs to cart",
            user_id="test_user",
            session_id="test_session"
        )
        print("✅ Message processing: SUCCESS")
        print(f"   Response: {response.get('message', 'No message')[:100]}...")
    except Exception as e:
        print(f"❌ Message processing: FAILED - {e}")
        return False
    
    # Test 3: Context building
    try:
        context = grocery_list_agent._build_context(
            user_profile={"diet": "vegetarian", "budget_limit": 50},
            context={"ingredients_needed": ["eggs", "milk"]},
            budget_limit=50.0
        )
        print("✅ Context building: SUCCESS")
        print(f"   Context preview: {context[:100]}...")
    except Exception as e:
        print(f"❌ Context building: FAILED - {e}")
        return False
    
    return True

def test_strands_entry_point():
    """Test the Strands entry point function"""
    print("\n🔧 Testing Strands Entry Point...")
    print("=" * 50)
    
    try:
        from agents.grocery_list_agent import strands_agent_bedrock
        
        payload = {"prompt": "Hello, I want to add milk to my cart"}
        response = strands_agent_bedrock(payload)
        
        print("✅ Strands entry point: SUCCESS")
        print(f"   Response: {response[:100]}...")
        return True
    except Exception as e:
        print(f"❌ Strands entry point: FAILED - {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting Grocery List Agent Tests")
    print("=" * 60)
    
    # Check if we can import the agent
    try:
        from agents.grocery_list_agent import grocery_list_agent
        print("✅ Import successful")
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return
    
    # Run tests
    basic_test = test_basic_functionality()
    strands_test = test_strands_entry_point()
    
    # Summary
    print("\n📊 Test Summary")
    print("=" * 60)
    if basic_test and strands_test:
        print("🎉 ALL TESTS PASSED! The grocery list agent is working.")
        print("\n💡 Next steps:")
        print("   - Add @tool decorated functions for cart management")
        print("   - Integrate with FastAPI routes")
        print("   - Test through frontend")
    else:
        print("⚠️  Some tests failed. Check the errors above.")
        print("\n🔧 Troubleshooting:")
        print("   - Make sure AWS credentials are configured")
        print("   - Check if DynamoDB tables exist")
        print("   - Verify all dependencies are installed")

if __name__ == "__main__":
    main()