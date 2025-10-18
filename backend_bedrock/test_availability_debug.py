#!/usr/bin/env python3
"""
Debug the check_item_availability function
"""

import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_availability():
    """Test the check_item_availability function"""
    print("🔍 Testing check_item_availability...")
    print("=" * 50)
    
    try:
        from tools.cart_tools.cart_manager import check_item_availability
        from tools.product_tools.registry import execute_catalog_tool
        
        # Test execute_catalog_tool directly first
        print("1. Testing execute_catalog_tool...")
        result = execute_catalog_tool("search_products", {"query": "eggs", "limit": 5})
        print(f"   execute_catalog_tool result: {result}")
        
        # Test check_item_availability
        print("\n2. Testing check_item_availability...")
        result = check_item_availability("eggs")
        print(f"   check_item_availability result: {result}")
        print(f"   Result type: {type(result)}")
        
        if result is None:
            print("❌ Function returned None!")
        elif result.get("success"):
            print("✅ Availability check works!")
        else:
            print(f"❌ Availability check failed: {result.get('error')}")
            
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_availability()