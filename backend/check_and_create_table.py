import boto3
from botocore.exceptions import ClientError

def check_and_create_table():
    """Check existing DynamoDB tables and create products table if needed"""
    
    # Initialize DynamoDB client
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    
    # List all tables
    print("📋 Existing DynamoDB tables:")
    for table in dynamodb.tables.all():
        print(f"  - {table.name}")
    
    # Check if products table exists
    table_name = 'products'
    try:
        table = dynamodb.Table(table_name)
        table.load()
        print(f"\n✅ Table '{table_name}' exists")
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            print(f"\n❌ Table '{table_name}' does not exist")
            return False
        else:
            print(f"❌ Error checking table: {e}")
            return False

if __name__ == "__main__":
    check_and_create_table() 