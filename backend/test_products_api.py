import requests
import json

def test_products_api():
    """Test the products API to check if images are being returned"""
    
    try:
        # Test the products API
        response = requests.get("http://localhost:8000/api/v1/products?limit=3")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Products API is working!")
            print(f"📊 Found {len(data.get('products', []))} products")
            
            # Check if products have image URLs
            products = data.get('products', [])
            for i, product in enumerate(products):
                print(f"\n📦 Product {i+1}: {product.get('name', 'Unknown')}")
                print(f"   Image URL: {product.get('image_url', 'No image')}")
                print(f"   Category: {product.get('category', 'No category')}")
        else:
            print(f"❌ API returned status code: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to the API. Make sure the server is running.")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_products_api() 