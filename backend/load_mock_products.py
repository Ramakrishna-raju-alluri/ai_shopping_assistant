#!/usr/bin/env python3
"""
Script to load mock products data into DynamoDB
"""

import json
import boto3
from decimal import Decimal
from dynamo.client import dynamodb, PRODUCT_TABLE
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def load_mock_products():
    """Load mock products data into DynamoDB"""
    
    # Read the mock products data
    with open('mock_products_data.json', 'r') as f:
        products_data = json.load(f)
    
    print(f"📊 Loading {len(products_data)} products into DynamoDB table: {PRODUCT_TABLE}")
    print("=" * 60)
    
    success_count = 0
    error_count = 0
    
    for product in products_data:
        try:
            # Convert price to Decimal for DynamoDB
            product['price'] = Decimal(str(product['price']))
            
            # Add the product to DynamoDB
            dynamodb.put_item(
                TableName=PRODUCT_TABLE,
                Item=product
            )
            
            print(f"✅ Loaded product: {product['name']} ({product['item_id']}) - ${product['price']}")
            success_count += 1
            
        except Exception as e:
            print(f"❌ Error loading product {product.get('item_id', 'unknown')}: {str(e)}")
            error_count += 1
    
    print("=" * 60)
    print(f"📈 Summary:")
    print(f"   ✅ Successfully loaded: {success_count} products")
    print(f"   ❌ Errors: {error_count} products")
    print(f"   📊 Total processed: {len(products_data)} products")
    
    # Print price distribution
    price_ranges = {
        "Budget ($0.99-2.99)": 0,
        "Mid-range ($3.00-6.99)": 0,
        "Premium ($7.00-12.99)": 0,
        "Luxury ($13.00+)": 0
    }
    
    for product in products_data:
        price = product['price']
        if price <= 2.99:
            price_ranges["Budget ($0.99-2.99)"] += 1
        elif price <= 6.99:
            price_ranges["Mid-range ($3.00-6.99)"] += 1
        elif price <= 12.99:
            price_ranges["Premium ($7.00-12.99)"] += 1
        else:
            price_ranges["Luxury ($13.00+)"] += 1
    
    print(f"\n💰 Price Distribution:")
    for range_name, count in price_ranges.items():
        print(f"   {range_name}: {count} products")
    
    # Print tag distribution
    tag_counts = {}
    for product in products_data:
        for tag in product['tags']:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1
    
    print(f"\n🏷️ Tag Distribution (Top 15):")
    sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
    for tag, count in sorted_tags[:15]:
        print(f"   {tag}: {count} products")
    
    # Print category distribution
    categories = {
        "Proteins": 0,
        "Vegetables": 0,
        "Fruits": 0,
        "Grains": 0,
        "Legumes": 0,
        "Nuts & Seeds": 0,
        "Dairy & Alternatives": 0,
        "Oils & Fats": 0
    }
    
    for product in products_data:
        tags = product['tags']
        if 'protein' in tags or 'high-protein' in tags:
            categories["Proteins"] += 1
        elif 'vegetable' in tags:
            categories["Vegetables"] += 1
        elif 'fruit' in tags:
            categories["Fruits"] += 1
        elif 'grain' in tags:
            categories["Grains"] += 1
        elif 'legume' in tags:
            categories["Legumes"] += 1
        elif any(tag in ['almonds', 'walnuts', 'seeds', 'nuts'] for tag in tags):
            categories["Nuts & Seeds"] += 1
        elif any(tag in ['dairy', 'milk', 'yogurt', 'cheese'] for tag in tags):
            categories["Dairy & Alternatives"] += 1
        elif any(tag in ['oil', 'butter', 'healthy-fats'] for tag in tags):
            categories["Oils & Fats"] += 1
    
    print(f"\n🥗 Category Distribution:")
    for category, count in categories.items():
        print(f"   {category}: {count} products")
    
    # Print dietary restriction coverage
    dietary_tags = ['vegan', 'vegetarian', 'gluten-free', 'keto', 'low-carb', 'organic']
    print(f"\n🥗 Dietary Restriction Coverage:")
    for diet in dietary_tags:
        count = sum(1 for product in products_data if diet in product['tags'])
        print(f"   {diet}: {count} products")
    
    print(f"\n🎉 Mock products data loading complete!")
    print(f"   Table: {PRODUCT_TABLE}")
    print(f"   You can now test the system with these products!")

if __name__ == "__main__":
    # Check if the JSON file exists
    if not os.path.exists('mock_products_data.json'):
        print("❌ Error: mock_products_data.json not found!")
        print("   Please make sure the file exists in the current directory.")
        exit(1)
    
    # Check if DynamoDB table exists
    try:
        dynamodb.describe_table(TableName=PRODUCT_TABLE)
        print(f"✅ Found DynamoDB table: {PRODUCT_TABLE}")
    except Exception as e:
        print(f"❌ Error: DynamoDB table {PRODUCT_TABLE} not found!")
        print(f"   Error: {str(e)}")
        print(f"   Please make sure the table exists and your AWS credentials are configured.")
        exit(1)
    
    # Load the data
    load_mock_products() 