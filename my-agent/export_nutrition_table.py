import boto3
import json
import os
from botocore.exceptions import ClientError

# -------- CONFIGURATION --------
AWS_REGION = "us-east-1"  # change if needed
NUTRITION_TABLE = "nutrition_calendar_fe7ed2"
OUTPUT_DIR = "dynamodb_exports"
# --------------------------------


def export_nutrition_table():
    """Export nutrition calendar table to JSON file"""
    
    # Create output directory if it doesn't exist
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Initialize DynamoDB client
    dynamodb = boto3.client("dynamodb", region_name=AWS_REGION)
    
    print(f"📦 Exporting nutrition table: {NUTRITION_TABLE} ...")
    
    items = []
    last_evaluated_key = None
    
    try:
        while True:
            # Scan the table
            if last_evaluated_key:
                response = dynamodb.scan(
                    TableName=NUTRITION_TABLE,
                    ExclusiveStartKey=last_evaluated_key
                )
            else:
                response = dynamodb.scan(TableName=NUTRITION_TABLE)
            
            # Add items to our list
            items.extend(response.get("Items", []))
            
            # Check if there are more items to scan
            last_evaluated_key = response.get("LastEvaluatedKey")
            if not last_evaluated_key:
                break
        
        # Save to JSON file
        output_file = os.path.join(OUTPUT_DIR, f"{NUTRITION_TABLE}.json")
        with open(output_file, "w") as f:
            json.dump(items, f, indent=2, default=str)
        
        print(f"✅ Successfully exported {len(items)} nutrition records to {output_file}")
        print(f"📁 File saved in: {os.path.abspath(output_file)}")
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            print(f"❌ Table {NUTRITION_TABLE} not found!")
            print("Make sure the table exists and the name is correct.")
        else:
            print(f"❌ Error exporting {NUTRITION_TABLE}: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


def main():
    """Main function"""
    print("🚀 Starting nutrition table export...")
    print(f"📊 Table: {NUTRITION_TABLE}")
    print(f"📂 Output directory: {OUTPUT_DIR}")
    print("-" * 50)
    
    export_nutrition_table()
    
    print("-" * 50)
    print("🎉 Export process completed!")


if __name__ == "__main__":
    main()