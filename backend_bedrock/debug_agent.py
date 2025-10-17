#!/usr/bin/env python3
"""
Debug script to test the grocery agent step by step
"""

import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_bedrock_model():
    """Test BedrockModel creation and methods"""
    print("🧠 Testing BedrockModel...")
    print("=" * 50)
    
    try:
        from strands.models import BedrockModel
        
        model = BedrockModel(
            model_id="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
            region_name="us-east-1",
        )
        
        print(f"✅ BedrockModel created successfully")
        print(f"Available methods: {[m for m in dir(model) if not m.startswith('_')]}")
        
        # Test a simple call
        test_prompt = "Say hello"
        
        # Try different methods
        methods_to_try = ['invoke', 'run', '__call__', 'chat', 'generate']
        
        for method_name in methods_to_try:
            if hasattr(model, method_name):
                print(f"✅ Model has method: {method_name}")
                try:
                    method = getattr(model, method_name)
                    if callable(method):
                        result = method(test_prompt)
                        print(f"✅ {method_name} worked: {str(result)[:100]}...")
                        break
                except Exception as e:
                    print(f"❌ {method_name} failed: {str(e)}")
            else:
                print(f"❌ Model does not have method: {method_name}")
                
    except Exception as e:
        print(f"❌ BedrockModel creation failed: {str(e)}")
        import traceback
        traceback.print_exc()

def test_agent_creation():
    """Test agent creation"""
    print("\n🤖 Testing Agent Creation...")
    print("=" * 50)
    
    try:
        from agents.grocery_list_agent import GroceryListAgent
        
        agent = GroceryListAgent()
        strands_agent = agent.get_agent()
        
        print(f"✅ Agent created successfully")
        print(f"Agent type: {type(strands_agent)}")
        print(f"Available methods: {[m for m in dir(strands_agent) if not m.startswith('_')]}")
        
    except Exception as e:
        print(f"❌ Agent creation failed: {str(e)}")
        import traceback
        traceback.print_exc()

def test_simple_message():
    """Test processing a simple message"""
    print("\n💬 Testing Simple Message...")
    print("=" * 50)
    
    try:
        from agents.grocery_list_agent import GroceryListAgent
        
        agent = GroceryListAgent()
        
        result = agent.process_message(
            user_message="add eggs to cart",
            user_id="test_user",
            session_id="test_session"
        )
        
        print(f"Result: {result}")
        
        if result.get("success"):
            print("✅ Message processed successfully")
        else:
            print(f"❌ Message processing failed: {result.get('error')}")
            if result.get('error_details'):
                print(f"Error details: {result.get('error_details')}")
                
    except Exception as e:
        print(f"❌ Message processing failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🔍 Debugging Grocery Agent Issues")
    print("=" * 70)
    
    test_bedrock_model()
    test_agent_creation()
    test_simple_message()
    
    print("\n🎯 Debug Complete!")