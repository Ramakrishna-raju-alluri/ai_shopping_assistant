#!/usr/bin/env python3
"""
Debug the get_user_profile function
"""

import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_user_profile():
    """Test the get_user_profile function"""
    print("👤 Testing get_user_profile...")
    print("=" * 50)
    
    try:
        from dynamo.queries import get_user_profile
        
        # Test with dummy user_id
        result = get_user_profile("user_id")
        print(f"get_user_profile result: {result}")
        print(f"Result type: {type(result)}")
        
        if result is None:
            print("❌ Function returned None!")
            print("This is the source of the error!")
        elif isinstance(result, dict):
            print("✅ Function returned dict")
            print(f"   Budget limit: {result.get('budget_limit', 100)}")
        else:
            print(f"❌ Unexpected return type: {type(result)}")
            
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        import traceback
        traceback.print_exc()

def test_budget_line():
    """Test the specific budget line that's failing"""
    print("\n💰 Testing budget calculation line...")
    print("=" * 50)
    
    try:
        from dynamo.queries import get_user_profile
        
        # Simulate the exact code from add_item_to_cart
        user_profile = get_user_profile("user_id") if "user_id" else {}
        print(f"user_profile: {user_profile}")
        print(f"user_profile type: {type(user_profile)}")
        
        if user_profile is None:
            print("❌ user_profile is None - this will cause the error!")
            return
            
        budget_limit = float(user_profile.get("budget_limit", 100))
        print(f"budget_limit: {budget_limit}")
        print("✅ Budget calculation successful!")
        
    except Exception as e:
        print(f"❌ Exception in budget calculation: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_user_profile()
    test_budget_line()