import boto3
import json
import os
from botocore.exceptions import ClientError
import time

# -------- CONFIGURATION --------
AWS_REGION = "us-east-1"  # change if needed
TABLES = [
    "mock-products2_with_calories",
    "mock-products2",
    "mock-recipes2",
    "mock-users2",
    "nutrition_calendar_fe7ed2"
]
IMPORT_DIR = "dynamodb_exports"

# Table primary key mapping
TABLE_KEYS = {
    "mock-products2_with_calories": "item_id",
    "mock-products2": "item_id", 
    "mock-recipes2": "recipe_id",
    "mock-users2": "user_id",
    "nutrition_calendar_fe7ed2": "date_user_id"
}


def delete_table_if_exists(dynamodb_client, table_name):
    """Delete a DynamoDB table if it exists"""
    try:
        print(f"🗑️  Checking if table {table_name} exists...")
        dynamodb_client.describe_table(TableName=table_name)
        
        # Table exists, delete it
        print(f"🗑️  Deleting existing table: {table_name} ...")
        dynamodb_client.delete_table(TableName=table_name)
        
        # Wait for table to be deleted
        print(f"⏳ Waiting for table {table_name} to be deleted...")
        waiter = dynamodb_client.get_waiter('table_not_exists')
        waiter.wait(TableName=table_name)
        print(f"✅ Table {table_name} deleted successfully!\n")
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            print(f"ℹ️  Table {table_name} doesn't exist, no need to delete.\n")
        else:
            print(f"❌ Error checking/deleting table {table_name}: {e}\n")
            raise


def create_table(dynamodb_client, table_name):
    """Create a DynamoDB table with correct primary key"""
    print(f"🔨 Creating table: {table_name} ...")
    
    # Get the correct primary key for this table
    primary_key = TABLE_KEYS.get(table_name, "id")
    
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
        print(f"✅ Table {table_name} created successfully!\n")
        
    except ClientError as e:
        print(f"❌ Error creating table {table_name}: {e}\n")
        raise


def get_users_from_json():
    """Get users from the mock-users2.json file"""
    users_file = os.path.join(IMPORT_DIR, "mock-users2.json")
    
    if not os.path.exists(users_file):
        print(f"⚠️  Users file not found: {users_file}, using default users")
        return [{"user_id": {"S": "user_101"}, "name": {"S": "user101"}},
                {"user_id": {"S": "user_102"}, "name": {"S": "user102"}},
                {"user_id": {"S": "user_103"}, "name": {"S": "user103"}}]
    
    with open(users_file, 'r') as f:
        users_data = json.load(f)
    
    # Extract user_id and name from each user
    users = []
    for user in users_data[:10]:  # Limit to first 10 users
        if 'user_id' in user and 'name' in user:
            users.append({
                'user_id': user['user_id']['S'],
                'name': user['name']['S']
            })
    
    return users


def create_sample_nutrition_data():
    """Create sample nutrition calendar data using real users"""
    from datetime import datetime, timedelta
    import random
    
    sample_data = []
    base_date = datetime.now()
    
    # Get real users from the JSON file
    users = get_users_from_json()
    print(f"📊 Creating nutrition data for {len(users)} users...")
    
    # Create 7 days of sample data for each user
    for day in range(7):
        current_date = (base_date - timedelta(days=day)).strftime("%Y-%m-%d")
        
        for user in users:
            user_id = user['user_id']
            user_name = user['name']
            date_user_id = f"{current_date}#{user_id}"
            
            # Vary nutrition targets slightly per user
            base_calories = random.randint(1800, 2200)
            protein_target = int(base_calories * 0.15 / 4)  # 15% of calories from protein
            carb_target = int(base_calories * 0.50 / 4)     # 50% of calories from carbs
            fat_target = int(base_calories * 0.35 / 9)      # 35% of calories from fat
            
            nutrition_entry = {
                "date_user_id": {"S": date_user_id},
                "date": {"S": current_date},
                "user_id": {"S": user_id},
                "user_name": {"S": user_name},
                "daily_targets": {
                    "M": {
                        "calories": {"N": str(base_calories)},
                        "protein": {"N": str(protein_target)},
                        "carbs": {"N": str(carb_target)},
                        "fat": {"N": str(fat_target)},
                        "fiber": {"N": str(random.randint(20, 30))},
                        "sugar": {"N": str(random.randint(40, 60))}
                    }
                },
                "meals": {
                    "L": [
                        {
                            "M": {
                                "meal_name": {"S": "Breakfast"},
                                "time": {"S": "08:00"},
                                "nutrition": {
                                    "M": {
                                        "calories": {"N": "450"},
                                        "protein": {"N": "25"},
                                        "carbs": {"N": "60"},
                                        "fat": {"N": "15"},
                                        "fiber": {"N": "8"},
                                        "sugar": {"N": "12"}
                                    }
                                },
                                "foods": {
                                    "L": [
                                        {"S": "Oatmeal with berries"},
                                        {"S": "Greek yogurt"},
                                        {"S": "Almonds"}
                                    ]
                                }
                            }
                        },
                        {
                            "M": {
                                "meal_name": {"S": "Lunch"},
                                "time": {"S": "12:30"},
                                "nutrition": {
                                    "M": {
                                        "calories": {"N": "650"},
                                        "protein": {"N": "45"},
                                        "carbs": {"N": "70"},
                                        "fat": {"N": "20"},
                                        "fiber": {"N": "10"},
                                        "sugar": {"N": "15"}
                                    }
                                },
                                "foods": {
                                    "L": [
                                        {"S": "Grilled chicken salad"},
                                        {"S": "Quinoa"},
                                        {"S": "Avocado"}
                                    ]
                                }
                            }
                        },
                        {
                            "M": {
                                "meal_name": {"S": "Dinner"},
                                "time": {"S": "19:00"},
                                "nutrition": {
                                    "M": {
                                        "calories": {"N": "750"},
                                        "protein": {"N": "55"},
                                        "carbs": {"N": "80"},
                                        "fat": {"N": "25"},
                                        "fiber": {"N": "12"},
                                        "sugar": {"N": "18"}
                                    }
                                },
                                "foods": {
                                    "L": [
                                        {"S": "Salmon fillet"},
                                        {"S": "Sweet potato"},
                                        {"S": "Steamed broccoli"}
                                    ]
                                }
                            }
                        }
                    ]
                },
                "daily_totals": {
                    "M": {
                        "calories": {"N": str(int(base_calories * random.uniform(0.85, 0.95)))},
                        "protein": {"N": str(int(protein_target * random.uniform(0.8, 1.1)))},
                        "carbs": {"N": str(int(carb_target * random.uniform(0.8, 1.1)))},
                        "fat": {"N": str(int(fat_target * random.uniform(0.8, 1.1)))},
                        "fiber": {"N": str(random.randint(18, 35))},
                        "sugar": {"N": str(random.randint(35, 55))}
                    }
                },
                "created_at": {"S": datetime.now().isoformat()},
                "updated_at": {"S": datetime.now().isoformat()}
            }
            
            sample_data.append(nutrition_entry)
    
    return sample_data


def import_data_from_json(dynamodb_client, table_name):
    """Import data from JSON file to DynamoDB table or create sample data for nutrition table"""
    
    # Special handling for nutrition calendar table
    if table_name == "nutrition_calendar_fe7ed2":
        print(f"📥 Creating sample nutrition data for table: {table_name} ...")
        items = create_sample_nutrition_data()
    else:
        json_file = os.path.join(IMPORT_DIR, f"{table_name}.json")
        
        if not os.path.exists(json_file):
            print(f"⚠️  JSON file not found: {json_file}, skipping import for {table_name}\n")
            return
        
        print(f"📥 Importing data to table: {table_name} ...")
        
        with open(json_file, 'r') as f:
            items = json.load(f)
        
        if not items:
            print(f"⚠️  No items found in {json_file}\n")
            return
    
    # Import items in batches
    batch_size = 25  # DynamoDB batch_write_item limit
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
    
    print(f"✅ Imported {len(items)} items to {table_name}\n")


def main():
    if not os.path.exists(IMPORT_DIR):
        print(f"❌ Import directory '{IMPORT_DIR}' not found!")
        return
    
    dynamodb = boto3.client("dynamodb", region_name=AWS_REGION)
    
    # Process tables in order - users table first, then nutrition table last
    ordered_tables = [
        "mock-users2",  # Process users first
        "mock-products2_with_calories",
        "mock-products2", 
        "mock-recipes2",
        "nutrition_calendar_fe7ed2"  # Process nutrition last so users data is available
    ]
    
    for table in ordered_tables:
        try:
            # Special handling for nutrition table - delete and recreate
            if table == "nutrition_calendar_fe7ed2":
                delete_table_if_exists(dynamodb, table)
                create_table(dynamodb, table)
            
            # Import data
            import_data_from_json(dynamodb, table)
            
        except Exception as e:
            print(f"❌ Error processing {table}: {e}\n")
            continue
    
    print(f"🎉 All data imported successfully!")


if __name__ == "__main__":
    main()