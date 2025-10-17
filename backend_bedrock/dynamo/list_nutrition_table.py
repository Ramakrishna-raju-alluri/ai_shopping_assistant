import os
import sys
import json
from pathlib import Path
from typing import Optional
from boto3.dynamodb.conditions import Key

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
        sys.path.insert(0, str(parent_dir))
        from dynamo.client import dynamodb, NUTRITION_TABLE
    except ImportError:
        import boto3
        dynamodb = boto3.resource("dynamodb")
        NUTRITION_TABLE = os.getenv("NUTRITION_TABLE", "nutrition_calendar")


def table():
    return dynamodb.Table(NUTRITION_TABLE)


def get_item(user_id: str, date: str):
    resp = table().get_item(Key={"user_id": user_id, "date": date})
    return resp.get("Item")


def query_user_days(user_id: str, limit: int = 100):
    resp = table().query(
        KeyConditionExpression=Key("user_id").eq(user_id),
        Limit=limit,
        ScanIndexForward=True,
    )
    return resp.get("Items", [])


def scan_all(limit: int = 100):
    t = table()
    items = []
    exclusive_start_key = None
    while True:
        kwargs = {"Limit": min(100, limit - len(items))}
        if exclusive_start_key:
            kwargs["ExclusiveStartKey"] = exclusive_start_key
        resp = t.scan(**kwargs)
        items.extend(resp.get("Items", []))
        exclusive_start_key = resp.get("LastEvaluatedKey")
        if not exclusive_start_key or len(items) >= limit:
            break
    return items[:limit]


def main():
    import argparse
    parser = argparse.ArgumentParser(description="List/query items from the nutrition calendar table")
    parser.add_argument("--user-id", dest="user_id", type=str, default=None, help="Filter by user_id")
    parser.add_argument("--date", dest="date", type=str, default=None, help="Fetch specific date (YYYY-MM-DD) requires --user-id")
    parser.add_argument("--limit", dest="limit", type=int, default=100, help="Max items to return for scans/queries")
    args = parser.parse_args()

    print(f"Using table: {NUTRITION_TABLE}")

    if args.user_id and args.date:
        item = get_item(args.user_id, args.date)
        print(json.dumps(item or {}, indent=2, default=str))
        return

    if args.user_id:
        items = query_user_days(args.user_id, args.limit)
        print(json.dumps(items, indent=2, default=str))
        return

    items = scan_all(args.limit)
    print(json.dumps(items, indent=2, default=str))


if __name__ == "__main__":
    main()


