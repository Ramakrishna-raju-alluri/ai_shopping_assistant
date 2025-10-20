import boto3
import json
import os
from botocore.exceptions import ClientError

# -------- CONFIGURATION --------
AWS_REGION = "us-east-1"  # change if needed
USER_CARTS_TABLE = "user_carts"
OUTPUT_DIR = "dynamodb_exports"
# --------------------------------


def export_user_carts_table():
    """Export user_carts table to JSON file"""
    
    # Create output directory if it doesn't exist
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Initialize DynamoDB client
    dynamodb = boto3.client("dynamodb", region_name=AWS_REGION)
    
    print(f"📦 Exporting user carts table: {USER_CARTS_TABLE} ...")
    
    items = []
    last_evaluated_key = None
    
    try:
        while True:
            # Scan the table
            if last_evaluated_key:
                response = dynamodb.scan(
                    TableName=USER_CARTS_TABLE,
                    ExclusiveStartKey=last_evaluated_key
                )
            else:
                response = dynamodb.scan(TableName=USER_CARTS_TABLE)
            
            # Add items to our list
            items.extend(response.get("Items", []))
            
            # Check if there are more items to scan
            last_evaluated_key = response.get("LastEvaluatedKey")
            if not last_evaluated_key:
                break
        
        # Save to JSON file
        output_file = os.path.join(OUTPUT_DIR, f"{USER_CARTS_TABLE}.json")
        with open(output_file, "w") as f:
            json.dump(items, f, indent=2, default=str)
        
        print(f"✅ Successfully exported {len(items)} cart records to {output_file}")
        print(f"📁 File saved in: {os.path.abspath(output_file)}")
        
        # Show sample of data structure
        if items:
            print(f"\n📋 Sample record structure:")
            sample_item = items[0]
            for key, value in sample_item.items():
                print(f"   {key}: {type(value).__name__}")
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            print(f"❌ Table {USER_CARTS_TABLE} not found!")
            print("Make sure the table exists and the name is correct.")
        else:
            print(f"❌ Error exporting {USER_CARTS_TABLE}: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


def main():
    """Main function"""
    print("🚀 Starting user_carts table export...")
    print(f"📊 Table: {USER_CARTS_TABLE}")
    print(f"📂 Output directory: {OUTPUT_DIR}")
    print("-" * 50)
    
    export_user_carts_table()
    
    print("-" * 50)
    print("🎉 Export process completed!")


if __name__ == "__main__":
    main()