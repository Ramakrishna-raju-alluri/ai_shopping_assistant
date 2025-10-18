#!/usr/bin/env python3
"""
Debug the search_products function
"""

import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_search_products():
    """Test the search_products function directly"""
    print("🔍 Testing search_products function...")
    print("=" * 50)
    
    try:
        from tools.product_tools.search import search_products
        
        # Test searching for eggs
        result = search_products("eggs", 5)
        print(f"Search result: {result}")
        
        if result.get("success"):
            products = result.get("products", [])
            print(f"✅ Found {len(products)} products")
            for product in products:
                print(f"   - {product.get('name')}: ${product.get('price')} (in_stock: {product.get('in_stock')})")
        else:
            print(f"❌ Search failed: {result.get('error')}")
            
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_search_products()