#!/usr/bin/env python3
"""
Script to load mock stock and promotional data into DynamoDB
"""

import json
import boto3
from decimal import Decimal
from dynamo.client import dynamodb, PROMO_TABLE
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def load_mock_stock_promo():
    """Load mock stock and promotional data into DynamoDB"""
    
    # Read the mock stock promo data
    with open('mock_stock_promo_data.json', 'r') as f:
        stock_promo_data = json.load(f)
    
    print(f"📊 Loading {len(stock_promo_data)} stock/promo entries into DynamoDB table: {PROMO_TABLE}")
    print("=" * 60)
    
    success_count = 0
    error_count = 0
    
    for entry in stock_promo_data:
        try:
            # Add the entry to DynamoDB
            dynamodb.put_item(
                TableName=PROMO_TABLE,
                Item=entry
            )
            
            status = "✅ In Stock" if entry['in_stock'] else "❌ Out of Stock"
            print(f"{status} - Item {entry['item_id']} - {entry['discount_percent']}% discount - Replace with {entry['replacement_suggestion']}")
            success_count += 1
            
        except Exception as e:
            print(f"❌ Error loading entry {entry.get('item_id', 'unknown')}: {str(e)}")
            error_count += 1
    
    print("=" * 60)
    print(f"📈 Summary:")
    print(f"   ✅ Successfully loaded: {success_count} entries")
    print(f"   ❌ Errors: {error_count} entries")
    print(f"   📊 Total processed: {len(stock_promo_data)} entries")
    
    # Print stock status distribution
    stock_status = {
        "In Stock": 0,
        "Out of Stock": 0
    }
    
    for entry in stock_promo_data:
        if entry['in_stock']:
            stock_status["In Stock"] += 1
        else:
            stock_status["Out of Stock"] += 1
    
    print(f"\n📦 Stock Status Distribution:")
    for status, count in stock_status.items():
        print(f"   {status}: {count} items")
    
    # Print discount distribution
    discount_ranges = {
        "Small (10-15%)": 0,
        "Medium (20-25%)": 0,
        "Large (30%)": 0
    }
    
    for entry in stock_promo_data:
        discount = entry['discount_percent']
        if discount <= 15:
            discount_ranges["Small (10-15%)"] += 1
        elif discount <= 25:
            discount_ranges["Medium (20-25%)"] += 1
        else:
            discount_ranges["Large (30%)"] += 1
    
    print(f"\n💰 Discount Distribution:")
    for range_name, count in discount_ranges.items():
        print(f"   {range_name}: {count} items")
    
    # Print replacement suggestion analysis
    replacement_counts = {}
    for entry in stock_promo_data:
        replacement = entry['replacement_suggestion']
        replacement_counts[replacement] = replacement_counts.get(replacement, 0) + 1
    
    print(f"\n🔄 Most Suggested Replacements:")
    sorted_replacements = sorted(replacement_counts.items(), key=lambda x: x[1], reverse=True)
    for replacement, count in sorted_replacements[:10]:
        print(f"   {replacement}: suggested {count} times")
    
    # Print in-stock vs out-of-stock discount analysis
    in_stock_discounts = []
    out_of_stock_discounts = []
    
    for entry in stock_promo_data:
        if entry['in_stock']:
            in_stock_discounts.append(entry['discount_percent'])
        else:
            out_of_stock_discounts.append(entry['discount_percent'])
    
    if in_stock_discounts:
        avg_in_stock = sum(in_stock_discounts) / len(in_stock_discounts)
        print(f"\n📊 Average discount for in-stock items: {avg_in_stock:.1f}%")
    
    if out_of_stock_discounts:
        avg_out_of_stock = sum(out_of_stock_discounts) / len(out_of_stock_discounts)
        print(f"📊 Average discount for out-of-stock items: {avg_out_of_stock:.1f}%")
    
    # Print item ID range analysis
    item_ids = [entry['item_id'] for entry in stock_promo_data]
    item_numbers = [int(item_id.split('_')[1]) for item_id in item_ids]
    
    print(f"\n🔢 Item ID Analysis:")
    print(f"   Range: item_{min(item_numbers):03d} to item_{max(item_numbers):03d}")
    print(f"   Total unique items: {len(set(item_ids))}")
    
    print(f"\n🎉 Mock stock/promo data loading complete!")
    print(f"   Table: {PROMO_TABLE}")
    print(f"   You can now test the system with stock and promotional features!")

if __name__ == "__main__":
    # Check if the JSON file exists
    if not os.path.exists('mock_stock_promo_data.json'):
        print("❌ Error: mock_stock_promo_data.json not found!")
        print("   Please make sure the file exists in the current directory.")
        exit(1)
    
    # Check if DynamoDB table exists
    try:
        dynamodb.describe_table(TableName=PROMO_TABLE)
        print(f"✅ Found DynamoDB table: {PROMO_TABLE}")
    except Exception as e:
        print(f"❌ Error: DynamoDB table {PROMO_TABLE} not found!")
        print(f"   Error: {str(e)}")
        print(f"   Please make sure the table exists and your AWS credentials are configured.")
        exit(1)
    
    # Load the data
    load_mock_stock_promo() 