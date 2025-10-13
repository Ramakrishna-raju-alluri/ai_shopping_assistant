#!/usr/bin/env python3
"""
Debug script to check product catalog issues
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import requests
import json
import time

def debug_product_catalog():
    """Debug product catalog issues"""
    
    print("🔍 Debugging Product Catalog Issues")
    print("=" * 50)
    
    base_url = "http://localhost:8000/api/v1"
    
    # Test user credentials
    test_user = {
        "username": f"debuguser_{int(time.time())}",
        "password": "testpass123",
        "name": "Debug User",
        "email": f"debuguser_{int(time.time())}@example.com"
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
        
        # Step 3: Check DynamoDB directly
        print(f"\n🗄️ Step 3: Checking DynamoDB directly...")
        try:
            from dynamo.client import dynamodb, PRODUCT_TABLE
            
            table = dynamodb.Table(PRODUCT_TABLE)
            response = table.scan()
            items = response.get('Items', [])
            
            print(f"   📦 Products in DynamoDB: {len(items)}")
            
            # Check for pagination
            while 'LastEvaluatedKey' in response:
                response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
                items.extend(response.get('Items', []))
                print(f"   📦 Additional products found: {len(response.get('Items', []))}")
            
            print(f"   📦 Total products in DynamoDB: {len(items)}")
            
            if items:
                print(f"   🛍️ Sample products from DynamoDB:")
                for i, item in enumerate(items[:5], 1):
                    print(f"     {i}. {item.get('name')} - ${item.get('price')} - {item.get('category', 'No category')}")
            
        except Exception as e:
            print(f"   ❌ Error checking DynamoDB: {e}")
        
        # Step 4: Test products API with different limits
        print(f"\n🛍️ Step 4: Testing products API...")
        
        # Test with limit=50
        products_response = requests.get(f"{base_url}/products?limit=50", headers=headers)
        if products_response.status_code == 200:
            products_data = products_response.json()
            print(f"   📦 Products returned (limit=50): {len(products_data.get('products', []))}")
            print(f"   📋 Total count (limit=50): {products_data.get('total_count', 0)}")
        
        # Test with limit=100
        products_response = requests.get(f"{base_url}/products?limit=100", headers=headers)
        if products_response.status_code == 200:
            products_data = products_response.json()
            print(f"   📦 Products returned (limit=100): {len(products_data.get('products', []))}")
            print(f"   📋 Total count (limit=100): {products_data.get('total_count', 0)}")
        
        # Test with no limit
        products_response = requests.get(f"{base_url}/products", headers=headers)
        if products_response.status_code == 200:
            products_data = products_response.json()
            print(f"   📦 Products returned (no limit): {len(products_data.get('products', []))}")
            print(f"   📋 Total count (no limit): {products_data.get('total_count', 0)}")
        
        # Step 5: Check categories
        print(f"\n📂 Step 5: Checking categories...")
        categories_response = requests.get(f"{base_url}/products/categories", headers=headers)
        if categories_response.status_code == 200:
            categories_data = categories_response.json()
            print(f"   📂 Categories found: {len(categories_data.get('categories', []))}")
            
            for category in categories_data.get('categories', []):
                print(f"     • {category.get('name')}: {category.get('product_count', 0)} products")
        
        # Step 6: Test category filtering
        print(f"\n🔍 Step 6: Testing category filtering...")
        categories_response = requests.get(f"{base_url}/products/categories", headers=headers)
        if categories_response.status_code == 200:
            categories_data = categories_response.json()
            
            for category in categories_data.get('categories', [])[:3]:  # Test first 3 categories
                category_name = category.get('name')
                if category_name and category_name != 'Uncategorized':
                    print(f"   🔍 Testing category: {category_name}")
                    category_response = requests.get(f"{base_url}/products?category={category_name}", headers=headers)
                    if category_response.status_code == 200:
                        category_data = category_response.json()
                        print(f"     📦 Products in {category_name}: {len(category_data.get('products', []))}")
        
        print(f"\n🎯 Debug completed!")
        
    except Exception as e:
        print(f"❌ Debug failed with error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_product_catalog() 