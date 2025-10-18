#!/usr/bin/env python3
"""
Debug the calc_cart_total function
"""

import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_cart_total():
    """Test the calc_cart_total function"""
    print("🛒 Testing calc_cart_total...")
    print("=" * 50)
    
    try:
        from tools.cart_tools.session_storage import calculate_cart_total as calc_cart_total
        
        # Test with a test session
        result = calc_cart_total("test_session")
        print(f"calc_cart_total result: {result}")
        print(f"Result type: {type(result)}")
        
        if result is None:
            print("❌ Function returned None!")
        elif isinstance(result, dict):
            print("✅ Function returned dict")
            if result.get("success"):
                print(f"   Total cost: {result.get('total_cost')}")
                print(f"   Item count: {result.get('item_count')}")
            else:
                print(f"   Error: {result.get('error')}")
        else:
            print(f"❌ Unexpected return type: {type(result)}")
            
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        import traceback
        traceback.print_exc()

def test_add_item_step_by_step():
    """Test add_item_to_cart step by step"""
    print("\n🔧 Testing add_item_to_cart step by step...")
    print("=" * 50)
    
    try:
        from tools.cart_tools.cart_manager import check_item_availability
        from tools.cart_tools.session_storage import calculate_cart_total as calc_cart_total
        
        # Step 1: Check availability
        print("1. Checking availability...")
        availability_result = check_item_availability("eggs")
        print(f"   Availability: {availability_result}")
        
        if not availability_result or not availability_result.get("success"):
            print("❌ Availability check failed")
            return
            
        # Step 2: Get available products
        available_products = availability_result.get("available_products", [])
        print(f"   Available products: {len(available_products)}")
        
        if not available_products:
            print("❌ No available products")
            return
            
        # Step 3: Get cart total
        print("2. Getting cart total...")
        current_cart = calc_cart_total("test_session")
        print(f"   Cart total result: {current_cart}")
        print(f"   Cart total type: {type(current_cart)}")
        
        if current_cart is None:
            print("❌ calc_cart_total returned None!")
            return
            
        # Step 4: Try to get total_cost
        print("3. Getting total cost...")
        current_total = current_cart.get("total_cost", 0.0)
        print(f"   Current total: {current_total}")
        
        print("✅ All steps completed successfully!")
        
    except Exception as e:
        print(f"❌ Exception in step-by-step test: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_cart_total()
    test_add_item_step_by_step()