#!/usr/bin/env python3
"""
Test script for the Coles Shopping Assistant Agent with Nova Pro
"""
import json
import sys
import os
import asyncio

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from main import invoke


async def test_nova_pro_agent():
    """Test the agent with Nova Pro integration"""
    
    # Set environment variables
    os.environ["AWS_REGION"] = "us-east-1"
    os.environ["USER_TABLE"] = "mock-users2"
    os.environ["PRODUCT_TABLE"] = "mock-products2"
    os.environ["NUTRITION_TABLE"] = "nutrition_calendar"
    
    test_cases = [
        {
            "name": "Product Stock Check",
            "payload": {
                "prompt": "Are bananas in stock?",
                "user_id": "test-user-123"
            }
        },
        {
            "name": "Set Daily Target",
            "payload": {
                "prompt": "Set my daily calorie target to 2000 for 2025-01-18",
                "user_id": "test-user-123"
            }
        },
        {
            "name": "Log Meal",
            "payload": {
                "prompt": "Log lunch with 600 calories for 2025-01-18",
                "user_id": "test-user-123"
            }
        },
        {
            "name": "Check Remaining Calories",
            "payload": {
                "prompt": "How many calories do I have left for 2025-01-18?",
                "user_id": "test-user-123"
            }
        }
    ]
    
    print("🧪 Testing Coles Shopping Assistant Agent with Nova Pro\n")
    print("=" * 60)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['name']}")
        print("-" * 40)
        print(f"Query: {test_case['payload']['prompt']}")
        
        try:
            result = await invoke(test_case['payload'])
            print(f"✅ Response: {result[:100]}...")
                
        except Exception as e:
            print(f"❌ Exception: {str(e)}")
    
    print("\n" + "=" * 60)
    print("🎉 Nova Pro testing completed!")


if __name__ == "__main__":
    asyncio.run(test_nova_pro_agent())
