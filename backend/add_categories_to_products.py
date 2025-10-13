#!/usr/bin/env python3
"""
Script to add categories to products based on their tags and names
"""

import json
import sys
import os

def add_categories_to_products():
    """Add category field to all products"""
    
    print("🏷️ Adding categories to products...")
    
    # Load current products
    with open('mock_products_data.json', 'r') as f:
        products = json.load(f)
    
    print(f"📦 Loaded {len(products)} products")
    
    # Define category mapping based on tags and names
    def get_category(product):
        name = product['name'].lower()
        tags = [tag.lower() for tag in product.get('tags', [])]
        
        # Protein category
        if any(tag in ['protein', 'meat', 'chicken', 'beef', 'pork', 'fish', 'salmon', 'tuna', 'turkey'] for tag in tags) or \
           any(word in name for word in ['chicken', 'beef', 'pork', 'fish', 'salmon', 'tuna', 'turkey', 'bacon', 'sausage']):
            return 'protein'
        
        # Dairy category
        if any(tag in ['dairy', 'milk', 'cheese', 'yogurt', 'butter', 'cream'] for tag in tags) or \
           any(word in name for word in ['milk', 'cheese', 'yogurt', 'butter', 'cream', 'feta', 'cheddar']):
            return 'dairy'
        
        # Vegetables category
        if any(tag in ['vegetable', 'vegetables'] for tag in tags) or \
           any(word in name for word in ['broccoli', 'spinach', 'cucumber', 'tomato', 'onion', 'carrot', 'lettuce', 'kale', 'cauliflower']):
            return 'vegetables'
        
        # Fruits category
        if any(tag in ['fruit', 'fruits'] for tag in tags) or \
           any(word in name for word in ['apple', 'banana', 'orange', 'strawberry', 'blueberry', 'avocado', 'mango', 'pineapple']):
            return 'fruits'
        
        # Grains category
        if any(tag in ['grain', 'grains'] for tag in tags) or \
           any(word in name for word in ['rice', 'quinoa', 'pasta', 'bread', 'oatmeal', 'cereal', 'flour']):
            return 'grains'
        
        # Nuts & Seeds category
        if any(tag in ['nuts', 'seeds'] for tag in tags) or \
           any(word in name for word in ['almond', 'walnut', 'cashew', 'peanut', 'sunflower', 'chia', 'flax', 'sesame']):
            return 'nuts-seeds'
        
        # Oils & Condiments category
        if any(tag in ['oil', 'condiment', 'sauce'] for tag in tags) or \
           any(word in name for word in ['oil', 'vinegar', 'sauce', 'ketchup', 'mustard', 'mayo']):
            return 'oils-condiments'
        
        # Organic category (if not already categorized)
        if 'organic' in tags:
            return 'organic'
        
        # Default category
        return 'other'
    
    # Add categories to products
    categorized_products = []
    category_counts = {}
    
    for product in products:
        category = get_category(product)
        product['category'] = category
        categorized_products.append(product)
        
        category_counts[category] = category_counts.get(category, 0) + 1
    
    # Save updated products
    with open('mock_products_data.json', 'w') as f:
        json.dump(categorized_products, f, indent=2)
    
    print(f"✅ Added categories to {len(categorized_products)} products")
    print(f"📂 Category distribution:")
    for category, count in sorted(category_counts.items()):
        print(f"   • {category}: {count} products")
    
    # Also update the DynamoDB table
    print(f"\n🔄 Updating DynamoDB table...")
    try:
        from dynamo.client import dynamodb, PRODUCT_TABLE
        from boto3.dynamodb.conditions import Attr
        
        table = dynamodb.Table(PRODUCT_TABLE)
        
        # Clear existing products
        print("   Clearing existing products...")
        response = table.scan()
        items = response.get('Items', [])
        
        for item in items:
            table.delete_item(Key={'item_id': item['item_id']})
        
        # Add updated products
        print("   Adding updated products...")
        from decimal import Decimal
        
        for product in categorized_products:
            # Convert price to Decimal
            if 'price' in product:
                product['price'] = Decimal(str(product['price']))
            table.put_item(Item=product)
        
        print(f"   ✅ Updated {len(categorized_products)} products in DynamoDB")
        
    except Exception as e:
        print(f"   ❌ Error updating DynamoDB: {e}")
        print(f"   💡 You may need to run load_mock_products.py to update the database")

if __name__ == "__main__":
    add_categories_to_products() 