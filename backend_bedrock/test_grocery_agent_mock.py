#!/usr/bin/env python3
"""
Mock test script for the Grocery List Agent (no AWS dependencies)
Run this to test the basic functionality without AWS credentials
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def mock_get_user_profile(user_id):
    """Mock user profile for testing"""
    return {
        "diet": "vegetarian",
        "budget_limit": 50.0,
        "allergies": ["nuts"],
        "preferred_cuisines": ["italian", "mexican"]
    }

def test_basic_structure():
    """Test basic agent structure without AWS calls"""
    print("🧪 Testing Grocery List Agent Structure...")
    print("=" * 50)
    
    # Test 1: Import and class structure
    try:
        # Mock the get_user_profile function
        import agents.grocery_list_agent as gla_module
        gla_module.get_user_profile = mock_get_user_profile
        
        from agents.grocery_list_agent import GroceryListAgent
        agent = GroceryListAgent()
        print("✅ Class structure: SUCCESS")
    except Exception as e:
        print(f"❌ Class structure: FAILED - {e}")
        return False
    
    # Test 2: Context building (no AWS needed)
    try:
        context = agent._build_context(
            user_profile={"diet": "vegetarian", "budget_limit": 50},
            context={"ingredients_needed": ["eggs", "milk"]},
            budget_limit=50.0
        )
        print("✅ Context building: SUCCESS")
        print(f"   Context preview: {context[:100]}...")
    except Exception as e:
        print(f"❌ Context building: FAILED - {e}")
        return False
    
    # Test 3: Agent initialization (this might fail due to AWS, but that's expected)
    try:
        strands_agent = agent.get_agent()
        print("✅ Strands agent creation: SUCCESS")
    except Exception as e:
        print(f"⚠️  Strands agent creation: EXPECTED FAILURE (AWS credentials needed)")
        print(f"   Error: {str(e)[:100]}...")
    
    return True

def test_method_signatures():
    """Test that all required methods exist with correct signatures"""
    print("\n🔧 Testing Method Signatures...")
    print("=" * 50)
    
    try:
        from agents.grocery_list_agent import GroceryListAgent
        agent = GroceryListAgent()
        
        # Check required methods exist
        methods_to_check = [
            'get_agent',
            'process_message',
            '_build_context',
            'create_grocery_list',
            'suggest_substitutions'
        ]
        
        for method_name in methods_to_check:
            if hasattr(agent, method_name):
                print(f"✅ Method '{method_name}': EXISTS")
            else:
                print(f"❌ Method '{method_name}': MISSING")
                return False
        
        return True
    except Exception as e:
        print(f"❌ Method signature test: FAILED - {e}")
        return False

def test_cart_tools():
    """Test that cart tools can be imported"""
    print("\n🛒 Testing Cart Tools...")
    print("=" * 50)
    
    try:
        from tools.cart_tools.registry import CART_TOOL_FUNCTIONS, CART_TOOLS
        print(f"✅ Cart tools imported: {len(CART_TOOL_FUNCTIONS)} functions")
        
        # Check each tool function
        tool_names = [func.__name__ for func in CART_TOOL_FUNCTIONS]
        expected_tools = [
            'add_item_to_cart',
            'get_cart_summary', 
            'remove_item_from_cart',
            'find_substitutes_for_item',
            'check_budget_status'
        ]
        
        for tool_name in expected_tools:
            if tool_name in tool_names:
                print(f"✅ Tool '{tool_name}': AVAILABLE")
            else:
                print(f"❌ Tool '{tool_name}': MISSING")
                return False
        
        return True
    except Exception as e:
        print(f"❌ Cart tools test: FAILED - {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting Grocery List Agent Mock Tests")
    print("=" * 60)
    print("ℹ️  This test runs without AWS credentials")
    print("=" * 60)
    
    # Run tests
    structure_test = test_basic_structure()
    method_test = test_method_signatures()
    cart_test = test_cart_tools()
    
    # Summary
    print("\n📊 Test Summary")
    print("=" * 60)
    if structure_test and method_test and cart_test:
        print("🎉 BASIC STRUCTURE TESTS PASSED!")
        print("\n💡 Next steps:")
        print("   - Configure AWS credentials to test full functionality")
        print("   - Add @tool decorated functions for cart management")
        print("   - Test with real DynamoDB data")
        print("\n🔧 To test with AWS:")
        print("   - Set up AWS credentials (aws configure)")
        print("   - Ensure DynamoDB tables exist")
        print("   - Run: python test_grocery_agent.py")
    else:
        print("⚠️  Some basic structure tests failed.")
        print("   Check the errors above and fix the code structure.")

if __name__ == "__main__":
    main()