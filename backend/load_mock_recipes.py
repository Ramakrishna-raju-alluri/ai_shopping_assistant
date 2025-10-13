#!/usr/bin/env python3
"""
Script to load mock recipes data into DynamoDB
"""

import json
import boto3
from decimal import Decimal
from dynamo.client import dynamodb, RECIPE_TABLE
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def load_mock_recipes():
    """Load mock recipes data into DynamoDB"""
    
    # Read the mock recipes data
    with open('mock_recipes_data.json', 'r') as f:
        recipes_data = json.load(f)
    
    print(f"📊 Loading {len(recipes_data)} recipes into DynamoDB table: {RECIPE_TABLE}")
    print("=" * 60)
    
    success_count = 0
    error_count = 0
    
    for recipe in recipes_data:
        try:
            # Convert total_cost to Decimal for DynamoDB
            recipe['total_cost'] = Decimal(str(recipe['total_cost']))
            
            # Add the recipe to DynamoDB
            dynamodb.put_item(
                TableName=RECIPE_TABLE,
                Item=recipe
            )
            
            print(f"✅ Loaded recipe: {recipe['title']} ({recipe['recipe_id']}) - ${recipe['total_cost']}")
            success_count += 1
            
        except Exception as e:
            print(f"❌ Error loading recipe {recipe.get('recipe_id', 'unknown')}: {str(e)}")
            error_count += 1
    
    print("=" * 60)
    print(f"📈 Summary:")
    print(f"   ✅ Successfully loaded: {success_count} recipes")
    print(f"   ❌ Errors: {error_count} recipes")
    print(f"   📊 Total processed: {len(recipes_data)} recipes")
    
    # Print cost distribution
    cost_ranges = {
        "Budget ($10-20)": 0,
        "Mid-range ($20-30)": 0,
        "Premium ($30-40)": 0,
        "Luxury ($40+)": 0
    }
    
    for recipe in recipes_data:
        cost = recipe['total_cost']
        if cost <= 20:
            cost_ranges["Budget ($10-20)"] += 1
        elif cost <= 30:
            cost_ranges["Mid-range ($20-30)"] += 1
        elif cost <= 40:
            cost_ranges["Premium ($30-40)"] += 1
        else:
            cost_ranges["Luxury ($40+)"] += 1
    
    print(f"\n💰 Cost Distribution:")
    for range_name, count in cost_ranges.items():
        print(f"   {range_name}: {count} recipes")
    
    # Print diet distribution
    diet_counts = {}
    for recipe in recipes_data:
        for diet in recipe['diet']:
            diet_counts[diet] = diet_counts.get(diet, 0) + 1
    
    print(f"\n🥗 Diet Distribution:")
    for diet, count in sorted(diet_counts.items()):
        print(f"   {diet}: {count} recipes")
    
    # Print cook time distribution
    cook_time_ranges = {
        "Quick (5-15 mins)": 0,
        "Medium (15-30 mins)": 0,
        "Long (30+ mins)": 0
    }
    
    for recipe in recipes_data:
        cook_time = recipe['cook_time_mins']
        if cook_time <= 15:
            cook_time_ranges["Quick (5-15 mins)"] += 1
        elif cook_time <= 30:
            cook_time_ranges["Medium (15-30 mins)"] += 1
        else:
            cook_time_ranges["Long (30+ mins)"] += 1
    
    print(f"\n⏱️ Cook Time Distribution:")
    for range_name, count in cook_time_ranges.items():
        print(f"   {range_name}: {count} recipes")
    
    # Print ingredient count distribution
    ingredient_counts = {}
    for recipe in recipes_data:
        count = len(recipe['ingredients'])
        ingredient_counts[count] = ingredient_counts.get(count, 0) + 1
    
    print(f"\n🥘 Ingredient Count Distribution:")
    for count, num_recipes in sorted(ingredient_counts.items()):
        print(f"   {count} ingredients: {num_recipes} recipes")
    
    # Print recipe type distribution
    recipe_types = {
        "Bowls": 0,
        "Salads": 0,
        "Stir-Fries": 0,
        "Curries": 0,
        "Soups": 0,
        "Other": 0
    }
    
    for recipe in recipes_data:
        title_lower = recipe['title'].lower()
        if 'bowl' in title_lower:
            recipe_types["Bowls"] += 1
        elif 'salad' in title_lower:
            recipe_types["Salads"] += 1
        elif 'stir-fry' in title_lower:
            recipe_types["Stir-Fries"] += 1
        elif 'curry' in title_lower:
            recipe_types["Curries"] += 1
        elif 'soup' in title_lower:
            recipe_types["Soups"] += 1
        else:
            recipe_types["Other"] += 1
    
    print(f"\n🍽️ Recipe Type Distribution:")
    for recipe_type, count in recipe_types.items():
        print(f"   {recipe_type}: {count} recipes")
    
    # Print average cost by diet
    diet_costs = {}
    for recipe in recipes_data:
        for diet in recipe['diet']:
            if diet not in diet_costs:
                diet_costs[diet] = []
            diet_costs[diet].append(float(recipe['total_cost']))
    
    print(f"\n💰 Average Cost by Diet:")
    for diet, costs in sorted(diet_costs.items()):
        avg_cost = sum(costs) / len(costs)
        print(f"   {diet}: ${avg_cost:.2f} average")
    
    print(f"\n🎉 Mock recipes data loading complete!")
    print(f"   Table: {RECIPE_TABLE}")
    print(f"   You can now test the system with these recipes!")

if __name__ == "__main__":
    # Check if the JSON file exists
    if not os.path.exists('mock_recipes_data.json'):
        print("❌ Error: mock_recipes_data.json not found!")
        print("   Please make sure the file exists in the current directory.")
        exit(1)
    
    # Check if DynamoDB table exists
    try:
        dynamodb.describe_table(TableName=RECIPE_TABLE)
        print(f"✅ Found DynamoDB table: {RECIPE_TABLE}")
    except Exception as e:
        print(f"❌ Error: DynamoDB table {RECIPE_TABLE} not found!")
        print(f"   Error: {str(e)}")
        print(f"   Please make sure the table exists and your AWS credentials are configured.")
        exit(1)
    
    # Load the data
    load_mock_recipes() 