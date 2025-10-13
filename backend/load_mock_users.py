#!/usr/bin/env python3
"""
Script to load mock users data into DynamoDB
"""

import json
import boto3
from decimal import Decimal
from dynamo.client import dynamodb, USER_TABLE
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def load_mock_users():
    """Load mock users data into DynamoDB"""
    
    # Read the mock users data
    with open('mock_users_data.json', 'r') as f:
        users_data = json.load(f)
    
    print(f"📊 Loading {len(users_data)} users into DynamoDB table: {USER_TABLE}")
    print("=" * 60)
    
    success_count = 0
    error_count = 0
    
    for user in users_data:
        try:
            # Convert budget_limit to Decimal for DynamoDB
            user['budget_limit'] = Decimal(str(user['budget_limit']))
            
            # Add the user to DynamoDB
            dynamodb.put_item(
                TableName=USER_TABLE,
                Item=user
            )
            
            print(f"✅ Loaded user: {user['name']} ({user['user_id']}) - Diet: {user['diet']}")
            success_count += 1
            
        except Exception as e:
            print(f"❌ Error loading user {user.get('user_id', 'unknown')}: {str(e)}")
            error_count += 1
    
    print("=" * 60)
    print(f"📈 Summary:")
    print(f"   ✅ Successfully loaded: {success_count} users")
    print(f"   ❌ Errors: {error_count} users")
    print(f"   📊 Total processed: {len(users_data)} users")
    
    # Print diet distribution
    diet_counts = {}
    for user in users_data:
        diet = user['diet']
        diet_counts[diet] = diet_counts.get(diet, 0) + 1
    
    print(f"\n🥗 Diet Distribution:")
    for diet, count in sorted(diet_counts.items()):
        print(f"   {diet}: {count} users")
    
    # Print budget distribution
    budget_ranges = {
        "Low ($60-80)": 0,
        "Medium ($80-120)": 0,
        "High ($120-170)": 0
    }
    
    for user in users_data:
        budget = user['budget_limit']
        if budget <= 80:
            budget_ranges["Low ($60-80)"] += 1
        elif budget <= 120:
            budget_ranges["Medium ($80-120)"] += 1
        else:
            budget_ranges["High ($120-170)"] += 1
    
    print(f"\n💰 Budget Distribution:")
    for range_name, count in budget_ranges.items():
        print(f"   {range_name}: {count} users")
    
    # Print meal goal distribution
    meal_goals = {}
    for user in users_data:
        goal = user['meal_goal']
        meal_goals[goal] = meal_goals.get(goal, 0) + 1
    
    print(f"\n🍽️ Meal Goal Distribution:")
    for goal, count in sorted(meal_goals.items()):
        print(f"   {goal}: {count} users")
    
    # Print shopping frequency distribution
    frequencies = {}
    for user in users_data:
        freq = user['shopping_frequency']
        frequencies[freq] = frequencies.get(freq, 0) + 1
    
    print(f"\n🛒 Shopping Frequency Distribution:")
    for freq, count in sorted(frequencies.items()):
        print(f"   {freq}: {count} users")
    
    print(f"\n🎉 Mock users data loading complete!")
    print(f"   Table: {USER_TABLE}")
    print(f"   You can now test the system with these users!")

if __name__ == "__main__":
    # Check if the JSON file exists
    if not os.path.exists('mock_users_data.json'):
        print("❌ Error: mock_users_data.json not found!")
        print("   Please make sure the file exists in the current directory.")
        exit(1)
    
    # Check if DynamoDB table exists
    try:
        dynamodb.describe_table(TableName=USER_TABLE)
        print(f"✅ Found DynamoDB table: {USER_TABLE}")
    except Exception as e:
        print(f"❌ Error: DynamoDB table {USER_TABLE} not found!")
        print(f"   Error: {str(e)}")
        print(f"   Please make sure the table exists and your AWS credentials are configured.")
        exit(1)
    
    # Load the data
    load_mock_users() 