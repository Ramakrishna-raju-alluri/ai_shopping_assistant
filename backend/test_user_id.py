#!/usr/bin/env python3
"""
Test script to debug user ID generation
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from routes.auth import generate_user_id
from dynamo.client import dynamodb, USER_TABLE
from boto3.dynamodb.conditions import Attr

def test_user_id_generation():
    """Test the user ID generation function"""
    print("🧪 Testing User ID Generation")
    print("=" * 50)
    
    # First, let's see what users exist in the database
    print("📊 Checking existing users in database...")
    table = dynamodb.Table(USER_TABLE)
    
    try:
        response = table.scan(
            ProjectionExpression="user_id, username, email",
            FilterExpression=Attr("user_id").begins_with("user_")
        )
        
        existing_users = response.get("Items", [])
        print(f"Found {len(existing_users)} existing users:")
        
        for user in existing_users:
            print(f"  - {user.get('user_id')} | {user.get('username')} | {user.get('email')}")
        
        if not existing_users:
            print("  No existing users found")
        
        print("\n" + "=" * 50)
        
        # Now test the user ID generation
        print("🔧 Testing generate_user_id() function...")
        new_user_id = generate_user_id()
        print(f"Generated user ID: {new_user_id}")
        
        # Verify it's greater than the maximum existing user ID
        try:
            user_num = int(new_user_id.split("_")[1])
            
            # Find the maximum existing user number
            existing_numbers = []
            for user in existing_users:
                try:
                    if user.get('user_id', '').startswith('user_'):
                        num = int(user.get('user_id').split('_')[1])
                        existing_numbers.append(num)
                except (IndexError, ValueError):
                    continue
            
            if existing_numbers:
                max_existing = max(existing_numbers)
                expected_next = max_existing + 1
                
                if user_num == expected_next:
                    print(f"✅ SUCCESS: User ID {new_user_id} is correct (max was {max_existing}, next should be {expected_next})")
                else:
                    print(f"❌ ERROR: User ID {new_user_id} is incorrect (max was {max_existing}, next should be {expected_next})")
            else:
                if user_num == 1:
                    print(f"✅ SUCCESS: User ID {new_user_id} is correct (first user)")
                else:
                    print(f"❌ ERROR: User ID {new_user_id} is incorrect (should be user_1 for first user)")
                    
        except (IndexError, ValueError):
            print(f"❌ ERROR: Invalid user ID format: {new_user_id}")
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")

if __name__ == "__main__":
    test_user_id_generation() 