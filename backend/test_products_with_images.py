import requests
import json

def test_products_with_images():
    """Test the products API to verify image URLs are being returned"""
    
    try:
        # Test the products API
        print("🔄 Testing products API...")
        response = requests.get("http://localhost:8000/api/v1/products?limit=5")
        
        if response.status_code == 200:
            data = response.json()
            products = data.get('products', [])
            
            print(f"✅ API Response Status: {response.status_code}")
            print(f"📊 Found {len(products)} products")
            
            # Check each product for image URLs
            for i, product in enumerate(products):
                print(f"\n📦 Product {i+1}: {product.get('name', 'Unknown')}")
                print(f"   Image URL: {product.get('image_url', '❌ NO IMAGE URL')}")
                print(f"   Category: {product.get('category', 'No category')}")
                print(f"   Price: ${product.get('price', 'N/A')}")
                
                # Check if image URL exists and is not empty
                image_url = product.get('image_url')
                if image_url and image_url.strip():
                    print(f"   ✅ Has image URL")
                else:
                    print(f"   ❌ Missing image URL")
                    
        else:
            print(f"❌ API returned status code: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to the API. Make sure the server is running.")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_products_with_images() 