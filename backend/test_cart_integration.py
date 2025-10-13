#!/usr/bin/env python3
"""
Test script to verify cart integration with chatbot
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import requests
import json
import time

def test_cart_integration():
    """Test the cart integration with chatbot"""
    
    print("🧪 Testing Cart Integration with Chatbot")
    print("=" * 60)
    
    base_url = "http://localhost:8000/api/v1"
    
    # Test user credentials
    test_user = {
        "username": f"testuser_{int(time.time())}",
        "password": "testpass123",
        "name": "Test User",
        "email": f"testuser_{int(time.time())}@example.com"
    }
    
    try:
        # Step 1: Create a test user
        print(f"\n🔐 Step 1: Creating test user...")
        signup_response = requests.post(f"{base_url}/auth/signup", json=test_user)
        
        if signup_response.status_code != 201:
            print(f"   ❌ Signup failed: {signup_response.status_code}")
            print(f"   Response: {signup_response.text}")
            return
        
        print(f"   ✅ User created successfully")
        
        # Step 2: Login to get token
        print(f"\n🔐 Step 2: Logging in...")
        login_data = {
            "username": test_user["username"],
            "password": test_user["password"]
        }
        login_response = requests.post(f"{base_url}/auth/login", json=login_data)
        
        if login_response.status_code != 200:
            print(f"   ❌ Login failed: {login_response.status_code}")
            print(f"   Response: {login_response.text}")
            return
        
        token = login_response.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}"}
        print(f"   ✅ Login successful")
        
        # Step 3: Send a meal planning message
        print(f"\n💬 Step 3: Sending meal planning message...")
        chat_message = {
            "message": "Plan 2 meals under $40",
            "session_id": None
        }
        
        chat_response = requests.post(f"{base_url}/chat", json=chat_message, headers=headers)
        
        if chat_response.status_code != 200:
            print(f"   ❌ Chat failed: {chat_response.status_code}")
            print(f"   Response: {chat_response.text}")
            return
        
        chat_data = chat_response.json()
        session_id = chat_data.get("session_id")
        print(f"   ✅ Chat response received")
        print(f"   📝 Session ID: {session_id}")
        print(f"   🛒 Requires confirmation: {chat_data.get('requires_confirmation')}")
        
        # Step 4: Check if cart options are available
        if chat_data.get("data", {}).get("add_to_cart_enabled"):
            print(f"   🎉 Cart options are available!")
            cart_options = chat_data.get("data", {}).get("cart_options", [])
            print(f"   📋 Available options: {cart_options}")
            
            # Step 5: Test "Add All to Cart" action
            print(f"\n🛒 Step 5: Testing 'Add All to Cart' action...")
            confirm_data = {
                "session_id": session_id,
                "confirmed": True,
                "feedback_data": {
                    "choice": "Add All to Cart"
                }
            }
            
            confirm_response = requests.post(f"{base_url}/confirm", json=confirm_data, headers=headers)
            
            if confirm_response.status_code != 200:
                print(f"   ❌ Cart action failed: {confirm_response.status_code}")
                print(f"   Response: {confirm_response.text}")
                return
            
            confirm_data = confirm_response.json()
            print(f"   ✅ Cart action response received")
            print(f"   📝 Response: {confirm_data.get('assistant_message', 'No message')[:100]}...")
            
            # Step 6: Check user's cart
            print(f"\n📋 Step 6: Checking user's cart...")
            cart_response = requests.get(f"{base_url}/cart", headers=headers)
            
            if cart_response.status_code == 200:
                cart_data = cart_response.json()
                if cart_data.get("success"):
                    cart = cart_data.get("cart", {})
                    print(f"   ✅ Cart retrieved successfully")
                    print(f"   📦 Items in cart: {cart.get('total_items', 0)}")
                    print(f"   💰 Total cost: ${cart.get('total_cost', 0):.2f}")
                    
                    if cart.get('items'):
                        print(f"   🛍️ Items:")
                        for item in cart.get('items', []):
                            print(f"     • {item.get('name')} - ${item.get('price')} x {item.get('quantity')}")
                else:
                    print(f"   ❌ Cart retrieval failed: {cart_data.get('message')}")
            else:
                print(f"   ❌ Cart request failed: {cart_response.status_code}")
        
        else:
            print(f"   ⚠️ Cart options not available in this response")
            print(f"   📝 Response data: {json.dumps(chat_data.get('data', {}), indent=2)}")
        
        print(f"\n🎯 Cart integration test completed!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_cart_integration() 