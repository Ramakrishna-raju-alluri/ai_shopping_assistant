import boto3
import json
import os
import time
from botocore.exceptions import ClientError

# -------- CONFIGURATION --------
AWS_REGION = "us-east-1"  # change if needed
USER_CARTS_TABLE = "user_carts"
PRIMARY_KEY = "cart_key"  # Based on the data structure
IMPORT_DIR = "dynamodb_exports"
# --------------------------------


def create_user_carts_table(dynamodb_client):
    """Create user_carts table with correct primary key"""
    print(f"🔨 Creating table: {USER_CARTS_TABLE} with primary key: {PRIMARY_KEY}")
    
    try:
        response = dynamodb_client.create_table(
            TableName=USER_CARTS_TABLE,
            KeySchema=[
                {
                    'AttributeName': PRIMARY_KEY,
                    'KeyType': 'HASH'  # Partition key
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': PRIMARY_KEY,
                    'AttributeType': 'S'  # String
                }
            ],
            BillingMode='PAY_PER_REQUEST'  # On-demand billing
        )
        
        # Wait for table to be created
        print(f"⏳ Waiting for table {USER_CARTS_TABLE} to be active...")
        waiter = dynamodb_client.get_waiter('table_exists')
        waiter.wait(TableName=USER_CARTS_TABLE)
        print(f"✅ Table {USER_CARTS_TABLE} created successfully!")
        return True
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print(f"⚠️  Table {USER_CARTS_TABLE} already exists, skipping creation.")
            return True
        else:
            print(f"❌ Error creating table {USER_CARTS_TABLE}: {e}")
            return False


def import_user_carts_data(dynamodb_client):
    """Import user_carts data from JSON file to DynamoDB table"""
    json_file = os.path.join(IMPORT_DIR, f"{USER_CARTS_TABLE}.json")
    
    if not os.path.exists(json_file):
        print(f"❌ JSON file not found: {json_file}")
        return False
    
    print(f"📥 Importing data to table: {USER_CARTS_TABLE}...")
    
    with open(json_file, 'r') as f:
        items = json.load(f)
    
    if not items:
        print(f"⚠️  No items found in {json_file}")
        return False
    
    print(f"📊 Found {len(items)} cart items to import")
    
    # Debug: Check first item structure
    if items:
        first_item = items[0]
        print(f"🔍 First item keys: {list(first_item.keys())}")
        if PRIMARY_KEY in first_item:
            print(f"✅ Primary key '{PRIMARY_KEY}' found in data: {first_item[PRIMARY_KEY]}")
        else:
            print(f"❌ Primary key '{PRIMARY_KEY}' NOT found in data!")
            print(f"Available keys: {list(first_item.keys())}")
            return False
    
    # Try importing just one item first to test
    print(f"🧪 Testing with first item...")
    test_item = items[0]
    
    try:
        response = dynamodb_client.put_item(
            TableName=USER_CARTS_TABLE,
            Item=test_item
        )
        print(f"✅ Test item imported successfully!")
    except ClientError as e:
        print(f"❌ Test item failed: {e}")
        print(f"🔍 Item structure: {json.dumps(test_item, indent=2)}")
        return False
    
    # If test worked, import the rest in batches
    batch_size = 25  # DynamoDB batch_write_item limit
    imported_count = 1  # We already imported the test item
    failed_count = 0
    
    # Skip first item since we already imported it and validate all items
    remaining_items = items[1:]
    valid_items = []
    
    print(f"🔍 Validating remaining {len(remaining_items)} items...")
    for idx, item in enumerate(remaining_items):
        if PRIMARY_KEY not in item:
            print(f"⚠️  Item {idx+2} missing primary key '{PRIMARY_KEY}', skipping")
            failed_count += 1
            continue
        if not item[PRIMARY_KEY].get('S'):
            print(f"⚠️  Item {idx+2} has empty primary key value, skipping")
            failed_count += 1
            continue
        valid_items.append(item)
    
    print(f"✅ Found {len(valid_items)} valid items to import")
    
    for i in range(0, len(valid_items), batch_size):
        batch = valid_items[i:i + batch_size]
        
        request_items = {
            USER_CARTS_TABLE: [
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
                
            print(f"✅ Imported batch {i//batch_size + 1} ({len(batch)} items)")
                
        except ClientError as e:
            print(f"❌ Error importing batch to {USER_CARTS_TABLE}: {e}")
            # Try importing items one by one to identify the problematic item
            print("🔍 Trying items individually...")
            for j, problem_item in enumerate(batch):
                try:
                    dynamodb_client.put_item(TableName=USER_CARTS_TABLE, Item=problem_item)
                    print(f"✅ Individual item {j+1} imported")
                except ClientError as individual_error:
                    print(f"❌ Individual item {j+1} failed: {individual_error}")
                    print(f"🔍 Problem item cart_key: {problem_item.get(PRIMARY_KEY, 'MISSING')}")
                    failed_count += 1
            continue
    
    print(f"🎉 Import completed!")
    print(f"✅ Successfully imported: {imported_count} items")
    if failed_count > 0:
        print(f"❌ Failed to import: {failed_count} items")
    
    return True


def check_table_exists(dynamodb_client):
    """Check if user_carts table already exists"""
    try:
        response = dynamodb_client.describe_table(TableName=USER_CARTS_TABLE)
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            return False
        else:
            print(f"❌ Error checking table: {e}")
            return False


def delete_table_if_exists(dynamodb_client):
    """Delete user_carts table if it exists"""
    try:
        print(f"🗑️  Checking if table {USER_CARTS_TABLE} exists...")
        dynamodb_client.describe_table(TableName=USER_CARTS_TABLE)
        
        # Table exists, delete it
        print(f"🗑️  Deleting existing table: {USER_CARTS_TABLE} ...")
        dynamodb_client.delete_table(TableName=USER_CARTS_TABLE)
        
        # Wait for table to be deleted
        print(f"⏳ Waiting for table {USER_CARTS_TABLE} to be deleted...")
        waiter = dynamodb_client.get_waiter('table_not_exists')
        waiter.wait(TableName=USER_CARTS_TABLE)
        print(f"✅ Table {USER_CARTS_TABLE} deleted successfully!")
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            print(f"ℹ️  Table {USER_CARTS_TABLE} doesn't exist, no need to delete.")
        else:
            print(f"❌ Error checking/deleting table {USER_CARTS_TABLE}: {e}")
            raise


def main():
    """Main function to create table and import data"""
    print("🚀 Starting user_carts table upload...")
    print(f"📊 Table: {USER_CARTS_TABLE}")
    print(f"🔑 Primary Key: {PRIMARY_KEY}")
    print(f"📂 Import directory: {IMPORT_DIR}")
    print("=" * 60)
    
    # Initialize DynamoDB client
    dynamodb = boto3.client("dynamodb", region_name=AWS_REGION)
    
    # Delete existing table if it exists (to fix schema issues)
    delete_table_if_exists(dynamodb)
    
    # Create table with correct schema
    if not create_user_carts_table(dynamodb):
        print("❌ Failed to create table. Exiting.")
        return
    
    # Import data
    if import_user_carts_data(dynamodb):
        print("\n🎉 User carts table has been successfully created and populated!")
        print(f"📋 Table: {USER_CARTS_TABLE}")
        print(f"🔑 Primary Key: {PRIMARY_KEY}")
        print("✅ Ready to use with your shopping assistant!")
    else:
        print("❌ Failed to import data.")
    
    print("=" * 60)


if __name__ == "__main__":
    main()