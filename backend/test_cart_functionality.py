#!/usr/bin/env python3
"""
Test script to verify the new cart functionality
"""

import asyncio
from routes.chat import handle_cart_operation, SessionState
from datetime import datetime

async def test_cart_functionality():
    """Test cart operations"""
    
    # Test queries
    test_queries = [
        "add bananas to cart",
        "add 2 organic milk to my cart",
        "put cottage cheese in cart",
        "add organic strawberries to shopping cart",
        "add 3 organic walnuts to cart",
        "view cart",
        "show my cart"
    ]
    
    print("🛒 Testing Cart Functionality")
    print("=" * 50)
    
    for test_query in test_queries:
        print(f"\n📝 Query: {test_query}")
        print("-" * 30)
        
        # Create a mock session
        session = SessionState(
            user_id="test_user_123",
            message=test_query,
            current_step="conversation_start",
            step_number=1,
            feedback={},
            created_at=datetime.now(),
            last_updated=datetime.now()
        )
        
        # Test the cart operation handler
        try:
            response = await handle_cart_operation(
                session_id="test_session",
                session=session,
                current_user=None
            )
            
            print(f"✅ Success: {response.is_complete}")
            print(f"🔍 Step: {response.step}")
            print(f"📄 Message: {response.assistant_message}")
            
            if response.data and response.data.get("cart_operation"):
                print(f"🎯 Cart Operation: Success")
                if response.data.get("cart_info"):
                    cart_info = response.data["cart_info"]
                    print(f"   📦 Total Items: {cart_info.get('total_items', 0)}")
                    print(f"   💰 Total Cost: ${cart_info.get('total_cost', 0):.2f}")
                if response.data.get("product_info"):
                    product_info = response.data["product_info"]
                    print(f"   🛍️ Product: {product_info.get('name', 'N/A')}")
                    print(f"   💵 Price: ${product_info.get('price', 0):.2f}")
                if response.data.get("quantity"):
                    print(f"   📊 Quantity: {response.data['quantity']}")
            else:
                print("❌ Cart operation failed")
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()
        
        print()

if __name__ == "__main__":
    asyncio.run(test_cart_functionality()) 