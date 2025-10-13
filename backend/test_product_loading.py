#!/usr/bin/env python3
"""
Test script to check product loading and API functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import requests
import json

def test_product_loading():
    """Test product loading and API functionality"""
    
    print("🧪 Testing Product Loading and API")
    print("=" * 50)
    
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
            return
        
        token = login_response.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}"}
        print(f"   ✅ Login successful")
        
        # Step 3: Test products API
        print(f"\n🛍️ Step 3: Testing products API...")
        
        # Test getting all products
        products_response = requests.get(f"{base_url}/products?limit=100", headers=headers)
        
        if products_response.status_code != 200:
            print(f"   ❌ Products API failed: {products_response.status_code}")
            print(f"   Response: {products_response.text}")
            return
        
        products_data = products_response.json()
        print(f"   ✅ Products API response received")
        print(f"   📦 Products returned: {len(products_data.get('products', []))}")
        print(f"   📋 Total count: {products_data.get('total_count', 0)}")
        
        if products_data.get('products'):
            print(f"   🛍️ Sample products:")
            for i, product in enumerate(products_data['products'][:5], 1):
                print(f"     {i}. {product.get('name')} - ${product.get('price')}")
        
        # Step 4: Test categories API
        print(f"\n📂 Step 4: Testing categories API...")
        categories_response = requests.get(f"{base_url}/products/categories", headers=headers)
        
        if categories_response.status_code != 200:
            print(f"   ❌ Categories API failed: {categories_response.status_code}")
            return
        
        categories_data = categories_response.json()
        print(f"   ✅ Categories API response received")
        print(f"   📂 Categories found: {len(categories_data.get('categories', []))}")
        
        if categories_data.get('categories'):
            print(f"   📋 Categories:")
            for category in categories_data['categories']:
                print(f"     • {category.get('name')} ({category.get('product_count', 0)} products)")
        
        # Step 5: Test cart API
        print(f"\n🛒 Step 5: Testing cart API...")
        cart_response = requests.get(f"{base_url}/cart", headers=headers)
        
        if cart_response.status_code != 200:
            print(f"   ❌ Cart API failed: {cart_response.status_code}")
            return
        
        cart_data = cart_response.json()
        print(f"   ✅ Cart API response received")
        print(f"   📦 Items in cart: {cart_data.get('cart', {}).get('total_items', 0)}")
        print(f"   💰 Total cost: ${cart_data.get('cart', {}).get('total_cost', 0):.2f}")
        
        # Step 6: Test adding product to cart
        print(f"\n🛒 Step 6: Testing add to cart...")
        if products_data.get('products'):
            test_product = products_data['products'][0]
            
            add_to_cart_data = {
                "items": [{
                    "item_id": test_product.get('item_id'),
                    "name": test_product.get('name'),
                    "price": test_product.get('price'),
                    "quantity": 1
                }]
            }
            
            add_cart_response = requests.post(f"{base_url}/cart/add", json=add_to_cart_data, headers=headers)
            
            if add_cart_response.status_code != 200:
                print(f"   ❌ Add to cart failed: {add_cart_response.status_code}")
                print(f"   Response: {add_cart_response.text}")
                return
            
            add_cart_data = add_cart_response.json()
            print(f"   ✅ Add to cart successful")
            print(f"   📦 Items added: {add_cart_data.get('cart', {}).get('total_items', 0)}")
            print(f"   💰 Total cost: ${add_cart_data.get('cart', {}).get('total_cost', 0):.2f}")
            
            # Check cart again
            cart_response2 = requests.get(f"{base_url}/cart", headers=headers)
            cart_data2 = cart_response2.json()
            print(f"   📦 Updated cart items: {cart_data2.get('cart', {}).get('total_items', 0)}")
        
        print(f"\n🎯 Product loading test completed!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import time
    test_product_loading() 