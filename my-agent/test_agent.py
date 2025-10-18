#!/usr/bin/env python3
"""
Test script for the Coles Shopping Assistant Agent
"""
import json
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.main import handler


def test_agent():
    """Test various agent functionalities"""
    
    test_cases = [
        {
            "name": "Product Stock Check",
            "event": {
                "prompt": "Are bananas in stock?",
                "user_id": "test-user-123",
                "timestamp": "2025-01-18T00:00:00Z"
            }
        },
        {
            "name": "Set Daily Target",
            "event": {
                "prompt": "Set my daily calorie target to 2000 for 2025-01-18",
                "user_id": "test-user-123",
                "timestamp": "2025-01-18T00:00:00Z"
            }
        },
        {
            "name": "Log Meal",
            "event": {
                "prompt": "Log lunch with 600 calories for 2025-01-18",
                "user_id": "test-user-123",
                "timestamp": "2025-01-18T00:00:00Z"
            }
        },
        {
            "name": "Check Remaining Calories",
            "event": {
                "prompt": "How many calories do I have left for 2025-01-18?",
                "user_id": "test-user-123",
                "timestamp": "2025-01-18T00:00:00Z"
            }
        },
        {
            "name": "Get Nutrition Summary",
            "event": {
                "prompt": "Show my nutrition summary for 2025-01-18",
                "user_id": "test-user-123",
                "timestamp": "2025-01-18T00:00:00Z"
            }
        }
    ]
    
    print("🧪 Testing Coles Shopping Assistant Agent\n")
    print("=" * 60)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['name']}")
        print("-" * 40)
        print(f"Query: {test_case['event']['prompt']}")
        
        try:
            result = handler(test_case['event'])
            
            if result['statusCode'] == 200:
                response_data = json.loads(result['body'])
                print(f"✅ Response: {response_data['response'][:100]}...")
            else:
                print(f"❌ Error: {result['body']}")
                
        except Exception as e:
            print(f"❌ Exception: {str(e)}")
    
    print("\n" + "=" * 60)
    print("🎉 Testing completed!")


if __name__ == "__main__":
    test_agent()
