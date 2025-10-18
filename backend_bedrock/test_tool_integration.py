#!/usr/bin/env python3
"""
Test tool integration with Strands agent
"""

import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_tool_functions():
    """Test the tool functions as they would be called by Strands"""
    print("🔧 Testing Tool Functions Integration...")
    print("=" * 50)
    
    try:
        from tools.product_tools.registry import PRODUCT_TOOL_FUNCTIONS
        from tools.cart_tools.registry import CART_TOOL_FUNCTIONS
        
        print(f"Product tools loaded: {len(PRODUCT_TOOL_FUNCTIONS)}")
        print(f"Cart tools loaded: {len(CART_TOOL_FUNCTIONS)}")
        
        # Test search_products tool directly
        for tool_func in PRODUCT_TOOL_FUNCTIONS:
            if hasattr(tool_func, '__name__') and tool_func.__name__ == 'search_products':
                print(f"\n🔍 Testing {tool_func.__name__}...")
                try:
                    result = tool_func("eggs", 5)
                    print(f"Result: {result}")
                    if result.get("success"):
                        print("✅ Tool function works!")
                    else:
                        print(f"❌ Tool failed: {result.get('error')}")
                except Exception as e:
                    print(f"❌ Exception calling tool: {str(e)}")
                    import traceback
                    traceback.print_exc()
                break
        
        # Test add_item_to_cart tool
        for tool_func in CART_TOOL_FUNCTIONS:
            if hasattr(tool_func, '__name__') and tool_func.__name__ == 'add_item_to_cart':
                print(f"\n🛒 Testing {tool_func.__name__}...")
                try:
                    result = tool_func("eggs", 1, "test_session")
                    print(f"Result: {result}")
                    if result.get("success"):
                        print("✅ Tool function works!")
                    else:
                        print(f"❌ Tool failed: {result.get('message', result.get('error'))}")
                except Exception as e:
                    print(f"❌ Exception calling tool: {str(e)}")
                    import traceback
                    traceback.print_exc()
                break
                
    except Exception as e:
        print(f"❌ Failed to load tools: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_tool_functions()