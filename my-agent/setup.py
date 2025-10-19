#!/usr/bin/env python3
"""
Setup script for Coles Shopping Assistant Agent with DeepSeek
"""
import os
import sys

def setup_environment():
    """Setup environment variables for the agent"""
    
    print("🔧 Setting up Coles Shopping Assistant Agent with Nova Pro")
    print("=" * 60)
    
    # Required environment variables
    env_vars = {
        "AWS_REGION": "us-east-1",
        "USER_TABLE": "mock-users2", 
        "PRODUCT_TABLE": "mock-products2",
        "RECIPE_TABLE": "mock-recipes2",
        "PROMO_TABLE": "promo_stock_feed2",
        "NUTRITION_TABLE": "nutrition_calendar"
        # No API key needed - using AWS Bedrock Nova Pro model
    }
    
    print("\n📋 Required Environment Variables:")
    print("-" * 40)
    
    for key, default_value in env_vars.items():
        current_value = os.getenv(key, "NOT SET")
        status = "✅" if current_value != "NOT SET" else "❌"
        print(f"{status} {key}: {current_value}")
        
        if current_value == "NOT SET":
            print(f"   Default: {default_value}")
    
    print("\n🚀 To set environment variables:")
    print("-" * 40)
    print("PowerShell:")
    for key, value in env_vars.items():
        print(f'$env:{key}="{value}"')
    
    print("\nBash:")
    for key, value in env_vars.items():
        print(f'export {key}="{value}"')
    
    print("\n⚠️  Important:")
    print("- Using Nova Pro model via AWS Bedrock (no external API key needed)")
    print("- Ensure DynamoDB tables exist and are accessible")
    print("- Verify AWS credentials are configured")
    print("- Ensure Bedrock access is enabled for Nova Pro model")
    
    print("\n" + "=" * 60)
    print("🎉 Setup information displayed!")


if __name__ == "__main__":
    setup_environment()
