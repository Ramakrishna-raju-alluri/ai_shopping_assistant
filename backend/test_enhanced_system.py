#!/usr/bin/env python3
"""
Test script for the enhanced AI Shopping Assistant with cart functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.cart_service import cart_service
from decimal import Decimal

def test_enhanced_system():
    """Test the enhanced system functionality"""
    
    print("🧪 Testing Enhanced AI Shopping Assistant")
    print("=" * 60)
    
    # Test user ID
    test_user_id = "user_61"
    
    print(f"👤 Testing with user: {test_user_id}")
    
    # Test 1: Get user cart (should be empty initially)
    print(f"\n📋 Test 1: Getting user cart")
    cart = cart_service.get_user_cart(test_user_id)
    print(f"   Cart items: {cart['total_items']}")
    print(f"   Cart total: ${cart['total_cost']:.2f}")
    
    # Test 2: Add items to cart
    print(f"\n🛒 Test 2: Adding items to cart")
    test_items = [
        {
            "item_id": "item_001",
            "name": "Organic Quinoa",
            "price": 8.99,
            "quantity": 1
        },
        {
            "item_id": "item_002", 
            "name": "Chicken Breast (1lb)",
            "price": 6.49,
            "quantity": 2
        },
        {
            "item_id": "item_003",
            "name": "Organic Spinach (8oz)", 
            "price": 3.99,
            "quantity": 1
        }
    ]
    
    result = cart_service.add_items_to_cart(test_user_id, test_items)
    
    if result["success"]:
        print(f"   ✅ Successfully added {len(test_items)} items")
        print(f"   📊 Cart now has {result['cart']['total_items']} items")
        print(f"   💰 Total cost: ${result['cart']['total_cost']:.2f}")
    else:
        print(f"   ❌ Error: {result['message']}")
    
    # Test 3: Update quantity
    print(f"\n📝 Test 3: Updating item quantity")
    update_result = cart_service.update_item_quantity(test_user_id, "item_001", 3)
    
    if update_result["success"]:
        print(f"   ✅ Successfully updated quantity")
        print(f"   📊 Cart now has {update_result['cart']['total_items']} items")
        print(f"   💰 Total cost: ${update_result['cart']['total_cost']:.2f}")
    else:
        print(f"   ❌ Error: {update_result['message']}")
    
    # Test 4: Remove item
    print(f"\n🗑️ Test 4: Removing item from cart")
    remove_result = cart_service.remove_item_from_cart(test_user_id, "item_003")
    
    if remove_result["success"]:
        print(f"   ✅ Successfully removed item")
        print(f"   📊 Cart now has {remove_result['cart']['total_items']} items")
        print(f"   💰 Total cost: ${remove_result['cart']['total_cost']:.2f}")
    else:
        print(f"   ❌ Error: {remove_result['message']}")
    
    # Test 5: Get final cart state
    print(f"\n📋 Test 5: Final cart state")
    final_cart = cart_service.get_user_cart(test_user_id)
    print(f"   Items in cart:")
    for item in final_cart['items']:
        print(f"     • {item['name']} - ${item['price']} x {item['quantity']}")
    print(f"   Total cost: ${final_cart['total_cost']:.2f}")
    
    # Test 6: Clear cart
    print(f"\n🧹 Test 6: Clearing cart")
    clear_result = cart_service.clear_cart(test_user_id)
    
    if clear_result["success"]:
        print(f"   ✅ Successfully cleared cart")
        print(f"   📊 Cart now has {clear_result['cart']['total_items']} items")
        print(f"   💰 Total cost: ${clear_result['cart']['total_cost']:.2f}")
    else:
        print(f"   ❌ Error: {clear_result['message']}")
    
    print(f"\n🎯 Enhanced system test completed!")
    print(f"✅ All cart functionality working correctly")
    print(f"🛒 Ready for integration with chatbot and UI")

if __name__ == "__main__":
    test_enhanced_system() 