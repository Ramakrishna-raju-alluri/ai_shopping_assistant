#!/usr/bin/env python3
"""
Test script to follow the complete meal planning flow to reach cart options
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import requests
import json
import time

def test_complete_meal_flow():
    """Test the complete meal planning flow to reach cart options"""
    
    print("🧪 Testing Complete Meal Planning Flow")
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
        
        # Step 3: Send initial meal planning message
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
        print(f"   📋 Query type: {chat_data.get('data', {}).get('query_type')}")
        
        # Step 4: Confirm the intent (if required)
        if chat_data.get("requires_confirmation"):
            print(f"\n✅ Step 4: Confirming intent...")
            confirm_data = {
                "session_id": session_id,
                "confirmed": True
            }
            
            confirm_response = requests.post(f"{base_url}/confirm", json=confirm_data, headers=headers)
            
            if confirm_response.status_code != 200:
                print(f"   ❌ Confirmation failed: {confirm_response.status_code}")
                print(f"   Response: {confirm_response.text}")
                return
            
            confirm_data = confirm_response.json()
            print(f"   ✅ Confirmation response received")
            print(f"   🛒 Requires confirmation: {confirm_data.get('requires_confirmation')}")
            print(f"   📋 Step: {confirm_data.get('step')}")
            
            # Continue confirming until we reach the final cart
            step_count = 0
            current_response = confirm_data
            
            while current_response.get("requires_confirmation") and step_count < 10:
                step_count += 1
                print(f"\n🔄 Step 4.{step_count}: Continuing flow...")
                
                confirm_data = {
                    "session_id": session_id,
                    "confirmed": True
                }
                
                confirm_response = requests.post(f"{base_url}/confirm", json=confirm_data, headers=headers)
                
                if confirm_response.status_code != 200:
                    print(f"   ❌ Step failed: {confirm_response.status_code}")
                    print(f"   Response: {confirm_response.text}")
                    return
                
                current_response = confirm_response.json()
                print(f"   ✅ Step response received")
                print(f"   🛒 Requires confirmation: {current_response.get('requires_confirmation')}")
                print(f"   📋 Step: {current_response.get('step')}")
                print(f"   📝 Message: {current_response.get('assistant_message', '')[:100]}...")
                
                # Check if we've reached the final cart
                if current_response.get("data", {}).get("add_to_cart_enabled"):
                    print(f"   🎉 CART OPTIONS FOUND!")
                    cart_options = current_response.get("data", {}).get("cart_options", [])
                    print(f"   📋 Available options: {cart_options}")
                    
                    # Test "Add All to Cart" action
                    print(f"\n🛒 Testing 'Add All to Cart' action...")
                    cart_confirm_data = {
                        "session_id": session_id,
                        "confirmed": True,
                        "feedback_data": {
                            "choice": "Add All to Cart"
                        }
                    }
                    
                    cart_confirm_response = requests.post(f"{base_url}/confirm", json=cart_confirm_data, headers=headers)
                    
                    if cart_confirm_response.status_code != 200:
                        print(f"   ❌ Cart action failed: {cart_confirm_response.status_code}")
                        print(f"   Response: {cart_confirm_response.text}")
                        return
                    
                    cart_confirm_data = cart_confirm_response.json()
                    print(f"   ✅ Cart action response received")
                    print(f"   📝 Response: {cart_confirm_data.get('assistant_message', 'No message')[:100]}...")
                    
                    # Check user's cart
                    print(f"\n📋 Checking user's cart...")
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
                    
                    break
                
                # If we've reached the limit, break
                if step_count >= 10:
                    print(f"   ⚠️ Reached maximum steps, stopping flow")
                    break
        
        else:
            print(f"   ⚠️ No confirmation required, flow may be incomplete")
        
        print(f"\n🎯 Complete meal flow test completed!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_complete_meal_flow() 