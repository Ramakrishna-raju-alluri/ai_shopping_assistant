import boto3
import json
import os
import time
from botocore.exceptions import ClientError

# -------- CONFIGURATION --------
AWS_REGION = "us-east-1"
IMPORT_DIR = "dynamodb_exports"
EXPECTED_TABLES = {
    "mock-products2_with_calories": "item_id",
    "mock-products2": "item_id", 
    "mock-recipes2": "recipe_id",
    "mock-users2": "user_id",
    "nutrition_calendar_fe7ed2": "date_user_id"
}
# --------------------------------


def check_table_exists_and_key(dynamodb_client, table_name, expected_key):
    """Check if table exists and has the correct primary key"""
    try:
        # Get table description
        response = dynamodb_client.describe_table(TableName=table_name)
        table_info = response['Table']
        
        # Extract primary key information
        key_schema = table_info['KeySchema']
        primary_key = None
        
        for key in key_schema:
            if key['KeyType'] == 'HASH':  # Partition key
                primary_key = key['AttributeName']
                break
        
        # Check if primary key matches expected
        key_match = primary_key == expected_key
        
        return {
            'exists': True,
            'primary_key': primary_key,
            'expected_key': expected_key,
            'key_match': key_match,
            'table_status': table_info['TableStatus'],
            'item_count': table_info.get('ItemCount', 'Unknown'),
            'table_size': table_info.get('TableSizeBytes', 'Unknown')
        }
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            return {
                'exists': False,
                'primary_key': None,
                'expected_key': expected_key,
                'key_match': False,
                'error': 'Table not found'
            }
        else:
            return {
                'exists': False,
                'primary_key': None,
                'expected_key': expected_key,
                'key_match': False,
                'error': str(e)
            }


def create_table(dynamodb_client, table_name, primary_key):
    """Create a DynamoDB table with the specified primary key"""
    print(f"�C Creating table: {table_name} with primary key: {primary_key}")
    
    try:
        response = dynamodb_client.create_table(
            TableName=table_name,
            KeySchema=[
                {
                    'AttributeName': primary_key,
                    'KeyType': 'HASH'  # Partition key
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': primary_key,
                    'AttributeType': 'S'  # String
                }
            ],
            BillingMode='PAY_PER_REQUEST'  # On-demand billing
        )
        
        # Wait for table to be created
        print(f"⏳ Waiting for table {table_name} to be active...")
        waiter = dynamodb_client.get_waiter('table_exists')
        waiter.wait(TableName=table_name)
        print(f"✅ Table {table_name} created successfully!")
        return True
        
    except ClientError as e:
        print(f"❌ Error creating table {table_name}: {e}")
        return False


def import_data_to_table(dynamodb_client, table_name):
    """Import data from JSON file to DynamoDB table"""
    json_file = os.path.join(IMPORT_DIR, f"{table_name}.json")
    
    if not os.path.exists(json_file):
        print(f"⚠️  JSON file not found: {json_file}")
        return False
    
    print(f"📥 Importing data to table: {table_name}...")
    
    with open(json_file, 'r') as f:
        items = json.load(f)
    
    if not items:
        print(f"⚠️  No items found in {json_file}")
        return False
    
    # Import items in batches
    batch_size = 25  # DynamoDB batch_write_item limit
    imported_count = 0
    
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        
        request_items = {
            table_name: [
                {
                    'PutRequest': {
                        'Item': item
                    }
                } for item in batch
            ]
        }
        
        try:
            response = dynamodb_client.batch_write_item(RequestItems=request_items)
            imported_count += len(batch)
            
            # Handle unprocessed items
            while response.get('UnprocessedItems'):
                print("⏳ Retrying unprocessed items...")
                time.sleep(1)
                response = dynamodb_client.batch_write_item(
                    RequestItems=response['UnprocessedItems']
                )
                
        except ClientError as e:
            print(f"❌ Error importing batch to {table_name}: {e}")
            continue
    
    print(f"✅ Imported {imported_count} items to {table_name}")
    return True


def fix_missing_tables(dynamodb_client, missing_tables):
    """Create missing tables and import data"""
    print(f"\n🔧 FIXING {len(missing_tables)} MISSING TABLES...")
    print("=" * 60)
    
    for table_name, primary_key in missing_tables.items():
        print(f"\n🛠️  Processing: {table_name}")
        print("-" * 40)
        
        # Create table
        if create_table(dynamodb_client, table_name, primary_key):
            # Import data
            import_data_to_table(dynamodb_client, table_name)
        else:
            print(f"❌ Failed to create {table_name}")


def main():
    """Check all expected tables and fix missing ones"""
    print("🔍 Checking DynamoDB Tables...")
    print("=" * 80)
    
    # Initialize DynamoDB client
    dynamodb = boto3.client("dynamodb", region_name=AWS_REGION)
    
    all_good = True
    missing_tables = {}
    incorrect_key_tables = {}
    
    for table_name, expected_key in EXPECTED_TABLES.items():
        print(f"\n📋 Table: {table_name}")
        print("-" * 50)
        
        result = check_table_exists_and_key(dynamodb, table_name, expected_key)
        
        if result['exists']:
            print(f"✅ Status: EXISTS")
            print(f"📊 Table Status: {result['table_status']}")
            print(f"🔑 Primary Key: {result['primary_key']}")
            print(f"🎯 Expected Key: {result['expected_key']}")
            
            if result['key_match']:
                print(f"✅ Key Match: CORRECT")
            else:
                print(f"❌ Key Match: INCORRECT")
                incorrect_key_tables[table_name] = expected_key
                all_good = False
            
            if result.get('item_count') != 'Unknown':
                print(f"📈 Item Count: {result['item_count']}")
            if result.get('table_size') != 'Unknown':
                print(f"💾 Table Size: {result['table_size']} bytes")
                
        else:
            print(f"❌ Status: MISSING")
            print(f"🎯 Expected Key: {result['expected_key']}")
            if 'error' in result:
                print(f"⚠️  Error: {result['error']}")
            missing_tables[table_name] = expected_key
            all_good = False
    
    print("\n" + "=" * 80)
    
    if all_good:
        print("🎉 ALL TABLES EXIST WITH CORRECT PRIMARY KEYS!")
    else:
        if missing_tables:
            print(f"⚠️  FOUND {len(missing_tables)} MISSING TABLES:")
            for table, key in missing_tables.items():
                print(f"   - {table} (needs primary key: {key})")
        
        if incorrect_key_tables:
            print(f"⚠️  FOUND {len(incorrect_key_tables)} TABLES WITH INCORRECT KEYS:")
            for table, key in incorrect_key_tables.items():
                print(f"   - {table} (needs primary key: {key})")
        
        # Ask user if they want to fix missing tables
        if missing_tables:
            print(f"\n🤔 Do you want to create the missing tables and import data?")
            response = input("Enter 'yes' to proceed or 'no' to skip: ").lower().strip()
            
            if response in ['yes', 'y']:
                fix_missing_tables(dynamodb, missing_tables)
                print("\n🎉 Missing tables have been created and populated!")
            else:
                print("\n⏭️  Skipped creating missing tables.")
    
    print("=" * 80)


if __name__ == "__main__":
    main()