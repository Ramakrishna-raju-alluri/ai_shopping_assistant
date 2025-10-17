import os
import time
import sys
from pathlib import Path
import botocore

# Support running both as a module and as a script
current_dir = Path(__file__).resolve().parent
parent_dir = current_dir.parent
project_root = parent_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

try:
    from backend_bedrock.dynamo.client import dynamodb, NUTRITION_TABLE
except ImportError:
    try:
        # When running from backend_bedrock directory
        sys.path.insert(0, str(parent_dir))
        from dynamo.client import dynamodb, NUTRITION_TABLE
    except ImportError:
        # Fallback: construct a resource directly; use default table name
        import boto3
        dynamodb = boto3.resource("dynamodb")
        NUTRITION_TABLE = os.getenv("NUTRITION_TABLE", "nutrition_calendar")


def ensure_table(table_name: str) -> None:
    """Create the nutrition calendar table if it does not exist."""
    client = dynamodb.meta.client

    # Check if table exists
    try:
        client.describe_table(TableName=table_name)
        print(f"DynamoDB table already exists: {table_name}")
        return
    except botocore.exceptions.ClientError as e:
        error_code = e.response.get("Error", {}).get("Code")
        if error_code != "ResourceNotFoundException":
            raise

    # Create table (user_id HASH, date RANGE)
    print(f"Creating DynamoDB table: {table_name} ...")
    client.create_table(
        TableName=table_name,
        AttributeDefinitions=[
            {"AttributeName": "user_id", "AttributeType": "S"},
            {"AttributeName": "date", "AttributeType": "S"},
        ],
        KeySchema=[
            {"AttributeName": "user_id", "KeyType": "HASH"},
            {"AttributeName": "date", "KeyType": "RANGE"},
        ],
        BillingMode="PAY_PER_REQUEST",
    )

    # Wait until exists
    waiter = client.get_waiter('table_exists')
    waiter.wait(TableName=table_name)
    desc = client.describe_table(TableName=table_name)
    arn = desc["Table"]["TableArn"]
    status = desc["Table"]["TableStatus"]
    print(f"Created: {table_name} | Status: {status} | ARN: {arn}")


if __name__ == "__main__":
    table_name = os.getenv("NUTRITION_TABLE", NUTRITION_TABLE)
    ensure_table(table_name)


