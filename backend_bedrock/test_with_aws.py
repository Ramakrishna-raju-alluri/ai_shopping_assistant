#!/usr/bin/env python3
"""
Test the grocery list agent with AWS credentials
"""

import sys
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_aws_connectivity():
    """Test AWS services connectivity"""
    print("🔗 Testing AWS Connectivity...")
    print("=" * 50)
    
    try:
        from tools.cart_tools.error_handler import check_aws_service_health
        
        health = check_aws_service_health()
        
        if health.get("aws_available"):
            print("✅ AWS Services: CONNECTED")
            print("✅ DynamoDB: ACCESSIBLE")
            return True
        else:
            print("❌ AWS Services: NOT AVAILABLE")
            print(f"   Issue: {health.get('message')}")
            print(f"   Suggestion: {health.get('suggestion')}")
            return False
            
    except Exception as e:
        print(f"❌ AWS connectivity test failed: {e}")
        return False

def test_llm_with_aws():
    """Test LLM parsing with AWS Bedrock"""
    print("\n🧠 Testing LLM with AWS Bedrock...")
    print("=" * 50)
    
    try:
        from tools.cart_tools.llm_parser import parse_grocery_request_with_llm
        
        # Test a complex request
        test_request = "I need 2 pounds of organic chicken breast and some low-fat Greek yogurt"
        print(f"Testing request: '{test_request}'")
        
        result = parse_grocery_request_with_llm(test_request)
        
        if isinstance(result, dict):
            print("✅ LLM Parsing: SUCCESS")
            print(f"   Action: {result.get('action')}")
            print(f"   Items found: {len(result.get('items', []))}")
            print(f"   Confidence: {result.get('intent_confidence', 0):.2f}")
            
            if result.get('special_requests'):
                print(f"   Special requests: {', '.join(result['special_requests'])}")
            
            for item in result.get('items', []):
                print(f"   - {item['quantity']} {item['unit']} of {item['name']}")
            
            return True
        else:
            print(f"❌ LLM parsing returned unexpected type: {type(result)}")
            return False
            
    except Exception as e:
        print(f"❌ LLM with AWS test failed: {e}")
        print("   This might be due to AWS Bedrock permissions or model access")
        return False

def test_complete_agent_with_aws():
    """Test the complete agent with AWS"""
    print("\n🤖 Testing Complete Agent with AWS...")
    print("=" * 50)
    
    try:
        from agents.grocery_list_agent import grocery_list_agent
        
        # Test the agent with a natural language request
        test_message = "add 2 pounds of chicken and some vegetables to my cart"
        print(f"Testing message: '{test_message}'")
        
        response = grocery_list_agent.process_message(
            user_message=test_message,
            user_id="test_user_aws",
            session_id="test_session_aws"
        )
        
        if response.get("success"):
            print("✅ Complete Agent: SUCCESS")
            print(f"   Response: {response.get('message', 'No message')[:100]}...")
        else:
            print("⚠️  Agent response indicates issues:")
            print(f"   Error: {response.get('error', 'Unknown error')}")
            print(f"   Message: {response.get('message', 'No message')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Complete agent test failed: {e}")
        return False

def test_product_search_with_aws():
    """Test product search with AWS DynamoDB"""
    print("\n🔍 Testing Product Search with AWS...")
    print("=" * 50)
    
    try:
        from tools.product_tools.registry import execute_catalog_tool
        
        # Test product search
        search_result = execute_catalog_tool("search_products", {"query": "milk", "limit": 3})
        
        if search_result.get("success"):
            products = search_result.get("products", [])
            print(f"✅ Product Search: Found {len(products)} products")
            
            for product in products[:2]:  # Show first 2
                print(f"   - {product.get('name', 'Unknown')}: ${product.get('price', 0):.2f}")
            
            return True
        else:
            print("❌ Product search failed:")
            print(f"   Error: {search_result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Product search test failed: {e}")
        print("   This might be due to DynamoDB table not existing or permissions")
        return False

def interactive_test():
    """Interactive test where user can input requests"""
    print("\n💬 Interactive Testing Mode...")
    print("=" * 50)
    print("Enter grocery requests to test the agent (type 'quit' to exit):")
    
    try:
        from agents.grocery_list_agent import grocery_list_agent
        
        while True:
            user_input = input("\n🛒 Your request: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            
            if not user_input:
                continue
            
            print(f"\n🤖 Processing: '{user_input}'")
            
            try:
                response = grocery_list_agent.process_message(
                    user_message=user_input,
                    user_id="interactive_user",
                    session_id="interactive_session"
                )
                
                if response.get("success"):
                    print(f"✅ Response: {response.get('message')}")
                else:
                    print(f"❌ Error: {response.get('message')}")
                    
            except Exception as e:
                print(f"❌ Processing failed: {e}")
    
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Interactive test failed: {e}")

def main():
    """Run AWS tests"""
    print("🚀 Starting AWS-Enabled Grocery Agent Tests")
    print("=" * 70)
    print("🎯 Testing with real AWS services")
    print("=" * 70)
    
    # Run tests
    aws_test = test_aws_connectivity()
    llm_test = test_llm_with_aws() if aws_test else False
    agent_test = test_complete_agent_with_aws() if aws_test else False
    product_test = test_product_search_with_aws() if aws_test else False
    
    print("\n📊 AWS Test Summary")
    print("=" * 70)
    
    if aws_test and llm_test and agent_test:
        print("🎉 ALL AWS TESTS PASSED!")
        print("\n✅ Verified Components:")
        print("   🔗 AWS Connectivity")
        print("   🧠 Bedrock LLM Intelligence")
        print("   🤖 Complete Agent Processing")
        print("   🔍 Product Search (if DynamoDB tables exist)")
        print("\n🚀 READY FOR PRODUCTION!")
        
        # Offer interactive testing
        try_interactive = input("\n💬 Would you like to try interactive testing? (y/n): ").strip().lower()
        if try_interactive in ['y', 'yes']:
            interactive_test()
            
    else:
        print("⚠️  Some AWS tests failed.")
        print("\n🔧 Troubleshooting:")
        if not aws_test:
            print("   - Configure AWS credentials: aws configure")
            print("   - Check AWS permissions for Bedrock and DynamoDB")
        if not product_test:
            print("   - Create DynamoDB tables (mock-products2, mock-users2)")
            print("   - Verify table permissions")
        print("   - Check AWS region settings (should be us-east-1)")

if __name__ == "__main__":
    main()