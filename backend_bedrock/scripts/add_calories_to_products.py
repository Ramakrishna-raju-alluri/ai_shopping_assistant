#!/usr/bin/env python3
"""
Script to add calorie information to DynamoDB products table using AWS Bedrock LLM.
This script will:
1. Read existing products from DynamoDB
2. Use Bedrock to generate calorie estimates for products
3. Create a backup table (optional)
4. Update products with calorie information
"""

import os
import sys
import json
import boto3
from pathlib import Path
from typing import List, Dict, Any
from dotenv import load_dotenv

# Add parent directory to path for imports
current_dir = Path(__file__).resolve().parent
parent_dir = current_dir.parent
project_root = parent_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Load environment variables
env_path = parent_dir / ".env"
load_dotenv(dotenv_path=env_path)

from backend_bedrock.dynamo.client import dynamodb, PRODUCT_TABLE

class ProductCalorieUpdater:
    def __init__(self):
        self.dynamodb = dynamodb
        self.source_table_name = PRODUCT_TABLE
        self.new_table_name = f"{PRODUCT_TABLE}_with_calories"
        
        # Initialize Bedrock client
        self.bedrock_client = boto3.client(
            'bedrock-runtime',
            region_name=os.getenv("AWS_REGION", "us-east-1")
        )
        
        # Model ID for Claude
        self.model_id = "anthropic.claude-3-haiku-20240307-v1:0"
    
    def get_table_info(self):
        """Get basic information about the source products table"""
        try:
            table = self.dynamodb.Table(self.source_table_name)
            
            # Get a few sample items first to check if table exists and has data
            scan_response = table.scan(Limit=5)
            items = scan_response.get('Items', [])
            
            if not items:
                print(f"❌ No items found in table: {self.source_table_name}")
                return 0, []
            
            # Get table description using the client (not the table resource)
            dynamodb_client = boto3.client('dynamodb', region_name=os.getenv("AWS_REGION", "us-east-1"))
            table_desc = dynamodb_client.describe_table(TableName=self.source_table_name)
            item_count = table_desc['Table']['ItemCount']
            
            print(f"📊 Source Table: {self.source_table_name}")
            print(f"📈 Approximate item count: {item_count}")
            print(f"🎯 New Table: {self.new_table_name}")
            
            print(f"\n🔍 Sample items structure:")
            for i, item in enumerate(items[:3], 1):
                print(f"\nItem {i}:")
                print(f"  - item_id: {item.get('item_id')}")
                print(f"  - name: {item.get('name')}")
                print(f"  - category: {item.get('category')}")
                print(f"  - price: {item.get('price')}")
                print(f"  - tags: {item.get('tags', [])}")
                print(f"  - has calories: {'calories' in item}")
            
            return len(items), items
            
        except Exception as e:
            print(f"❌ Error getting table info: {e}")
            print(f"   Make sure table '{self.source_table_name}' exists and you have proper AWS credentials")
            return 0, []
    
    def create_new_table_with_calories(self):
        """Create a new table with calorie information"""
        try:
            source_table = self.dynamodb.Table(self.source_table_name)
            
            # Check if new table already exists
            try:
                new_table = self.dynamodb.Table(self.new_table_name)
                new_table.load()
                print(f"⚠️  New table {self.new_table_name} already exists")
                
                # Check if it has items
                dynamodb_client = boto3.client('dynamodb', region_name=os.getenv("AWS_REGION", "us-east-1"))
                response = dynamodb_client.describe_table(TableName=self.new_table_name)
                item_count = response['Table']['ItemCount']
                print(f"📊 Existing table has {item_count} items")
                
                user_input = input("Do you want to delete and recreate it? (y/N): ").strip().lower()
                if user_input == 'y':
                    print("🗑️  Deleting existing table...")
                    new_table.delete()
                    new_table.wait_until_not_exists()
                    print("✅ Table deleted")
                else:
                    return True
            except:
                pass
            
            # Get source table schema using client
            dynamodb_client = boto3.client('dynamodb', region_name=os.getenv("AWS_REGION", "us-east-1"))
            source_desc = dynamodb_client.describe_table(TableName=self.source_table_name)['Table']
            
            # Create new table with same schema
            print(f"🏗️  Creating new table: {self.new_table_name}")
            self.dynamodb.create_table(
                TableName=self.new_table_name,
                KeySchema=source_desc['KeySchema'],
                AttributeDefinitions=source_desc['AttributeDefinitions'],
                BillingMode='PAY_PER_REQUEST'
            )
            
            # Wait for table to be created
            new_table = self.dynamodb.Table(self.new_table_name)
            new_table.wait_until_exists()
            
            print(f"✅ Created new table: {self.new_table_name}")
            return True
            
        except Exception as e:
            print(f"❌ Error creating new table: {e}")
            return False
    
    def generate_calories_with_bedrock(self, products: List[Dict]) -> Dict[str, int]:
        """Generate calorie estimates for a batch of products using Bedrock"""
        
        # Prepare product list for LLM
        product_list = []
        for product in products:
            product_info = {
                "item_id": product.get("item_id"),
                "name": product.get("name"),
                "category": product.get("category", "unknown"),
                "tags": product.get("tags", [])
            }
            product_list.append(product_info)
        
        # Create prompt for structured output
        prompt = f"""
You are a nutrition expert. I need you to estimate the calories per 100g for each of the following food products.

Products to analyze:
{json.dumps(product_list, indent=2)}

Please provide your response as a valid JSON object with this exact structure:
{{
  "calories_estimates": {{
    "item_id_1": calories_per_100g_as_integer,
    "item_id_2": calories_per_100g_as_integer,
    ...
  }}
}}

Guidelines:
- Estimate calories per 100g (standard serving)
- Use realistic values based on the product name, category, and tags
- For packaged/processed foods, estimate based on typical nutritional content
- For fresh produce, use standard nutritional data
- Return only integers (no decimals)
- If unsure, use reasonable estimates based on similar products

Respond with ONLY the JSON object, no additional text.
"""

        try:
            # Prepare request for Bedrock
            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 2000,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            }
            
            # Call Bedrock
            response = self.bedrock_client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(request_body)
            )
            
            # Parse response
            response_body = json.loads(response['body'].read())
            llm_response = response_body['content'][0]['text']
            
            # Parse JSON response
            calories_data = json.loads(llm_response.strip())
            
            return calories_data.get('calories_estimates', {})
            
        except Exception as e:
            print(f"❌ Error calling Bedrock: {e}")
            return {}
    
    def test_calorie_generation(self, limit=5):
        """Test calorie generation on a small batch"""
        try:
            table = self.dynamodb.Table(self.source_table_name)
            
            # Get a small batch of products
            response = table.scan(Limit=limit)
            products = response.get('Items', [])
            
            if not products:
                print("❌ No products found in table")
                return
            
            print(f"\n🧪 Testing calorie generation on {len(products)} products...")
            
            # Generate calories
            calories_estimates = self.generate_calories_with_bedrock(products)
            
            print(f"\n📊 Generated calorie estimates:")
            for product in products:
                item_id = product.get('item_id')
                name = product.get('name')
                category = product.get('category')
                estimated_calories = calories_estimates.get(item_id, 'N/A')
                
                print(f"\n🍎 {name}")
                print(f"   ID: {item_id}")
                print(f"   Category: {category}")
                print(f"   Estimated calories/100g: {estimated_calories}")
                print(f"   Current has calories: {'calories' in product}")
            
            return calories_estimates
            
        except Exception as e:
            print(f"❌ Error in test: {e}")
            return {}
    
    def copy_products_with_calories(self, batch_size=10, dry_run=True):
        """Copy all products to new table with calorie information"""
        try:
            source_table = self.dynamodb.Table(self.source_table_name)
            new_table = self.dynamodb.Table(self.new_table_name)
            
            print(f"\n🔄 {'DRY RUN: ' if dry_run else ''}Copying products with calories to new table...")
            print(f"📦 Batch size: {batch_size}")
            print(f"📊 Source: {self.source_table_name}")
            print(f"🎯 Target: {self.new_table_name}")
            
            # Scan all products from source
            response = source_table.scan()
            all_products = response.get('Items', [])
            
            # Handle pagination
            while 'LastEvaluatedKey' in response:
                response = source_table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
                all_products.extend(response.get('Items', []))
            
            print(f"📊 Total products to process: {len(all_products)}")
            
            # Process in batches
            copied_count = 0
            for i in range(0, len(all_products), batch_size):
                batch = all_products[i:i + batch_size]
                
                print(f"\n🔄 Processing batch {i//batch_size + 1} ({len(batch)} items)...")
                
                # Generate calories for batch
                calories_estimates = self.generate_calories_with_bedrock(batch)
                
                if not dry_run:
                    # Copy each product with calories to new table
                    with new_table.batch_writer() as batch_writer:
                        for product in batch:
                            # Create new item with calories
                            new_item = dict(product)  # Copy all existing fields
                            item_id = product.get('item_id')
                            
                            # Add calories if generated
                            if item_id in calories_estimates:
                                new_item['calories'] = calories_estimates[item_id]
                            else:
                                new_item['calories'] = 0  # Default value if generation failed
                            
                            batch_writer.put_item(Item=new_item)
                            copied_count += 1
                
                print(f"✅ Batch completed. Generated {len(calories_estimates)} calorie estimates")
            
            if not dry_run:
                print(f"\n🎉 Copy completed! {copied_count} products copied with calories to {self.new_table_name}")
            else:
                print(f"\n🧪 DRY RUN completed. Would copy {len(all_products)} products with calories")
            
        except Exception as e:
            print(f"❌ Error copying products: {e}")

def main():
    print("🍎 Product Calorie Updater")
    print("=" * 50)
    
    updater = ProductCalorieUpdater()
    
    # Get table information
    print("\n1️⃣ Getting table information...")
    item_count, sample_items = updater.get_table_info()
    
    if item_count == 0:
        print("❌ No items found in table. Exiting.")
        return
    
    # Test calorie generation
    print("\n2️⃣ Testing calorie generation...")
    test_results = updater.test_calorie_generation(limit=3)
    
    if not test_results:
        print("❌ Calorie generation test failed. Exiting.")
        return
    
    # Ask user if they want to proceed
    print(f"\n3️⃣ Ready to process {item_count} products")
    print("Options:")
    print("  1. Create new table and run dry-run")
    print("  2. Create new table and copy all products with calories")
    print("  3. Exit")
    
    choice = input("\nEnter your choice (1-3): ").strip()
    
    if choice == "1":
        print("\n🏗️  Creating new table...")
        if updater.create_new_table_with_calories():
            print("\n🧪 Running dry-run...")
            updater.copy_products_with_calories(dry_run=True)
    elif choice == "2":
        print("\n🏗️  Creating new table...")
        if updater.create_new_table_with_calories():
            print("\n🚀 Copying all products with calories...")
            updater.copy_products_with_calories(dry_run=False)
    else:
        print("👋 Exiting...")

if __name__ == "__main__":
    main()