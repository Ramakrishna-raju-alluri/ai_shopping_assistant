#!/usr/bin/env python3
"""
Script to verify replacement suggestions are logical and relevant
"""

import json

def verify_replacements():
    """Verify that replacement suggestions make sense"""
    
    # Load the data
    with open('mock_products_data.json', 'r') as f:
        products_data = json.load(f)
    
    with open('mock_stock_promo_data.json', 'r') as f:
        stock_promo_data = json.load(f)
    
    # Create product lookup
    products_lookup = {product['item_id']: product for product in products_data}
    
    print("🔍 Verifying Replacement Suggestions")
    print("=" * 60)
    
    valid_replacements = 0
    total_replacements = len(stock_promo_data)
    
    for entry in stock_promo_data:
        item_id = entry['item_id']
        replacement_name = entry['replacement_suggestion']
        
        # Find the original product
        original_product = products_lookup.get(item_id)
        if not original_product:
            print(f"❌ ERROR: {item_id} not found in products data")
            continue
        
        # Find the replacement product
        replacement_product = None
        for product in products_data:
            if product['name'] == replacement_name:
                replacement_product = product
                break
        
        if not replacement_product:
            print(f"❌ ERROR: Replacement '{replacement_name}' not found in products data")
            continue
        
        # Analyze the replacement
        original_tags = set(original_product['tags'])
        replacement_tags = set(replacement_product['tags'])
        
        # Check for logical compatibility
        is_logical = False
        reasoning = []
        
        # Check dietary compatibility
        if 'vegan' in original_tags and 'vegan' in replacement_tags:
            is_logical = True
            reasoning.append("Both vegan")
        elif 'vegetarian' in original_tags and 'vegetarian' in replacement_tags:
            is_logical = True
            reasoning.append("Both vegetarian")
        elif 'gluten-free' in original_tags and 'gluten-free' in replacement_tags:
            is_logical = True
            reasoning.append("Both gluten-free")
        elif 'keto' in original_tags and 'keto' in replacement_tags:
            is_logical = True
            reasoning.append("Both keto-friendly")
        elif 'low-carb' in original_tags and 'low-carb' in replacement_tags:
            is_logical = True
            reasoning.append("Both low-carb")
        elif 'high-protein' in original_tags and 'high-protein' in replacement_tags:
            is_logical = True
            reasoning.append("Both high-protein")
        
        # Check category compatibility
        if 'protein' in original_tags and 'protein' in replacement_tags:
            is_logical = True
            reasoning.append("Both protein sources")
        elif 'vegetable' in original_tags and 'vegetable' in replacement_tags:
            is_logical = True
            reasoning.append("Both vegetables")
        elif 'fruit' in original_tags and 'fruit' in replacement_tags:
            is_logical = True
            reasoning.append("Both fruits")
        elif 'grain' in original_tags and 'grain' in replacement_tags:
            is_logical = True
            reasoning.append("Both grains")
        elif 'legume' in original_tags and 'legume' in replacement_tags:
            is_logical = True
            reasoning.append("Both legumes")
        elif 'healthy-fats' in original_tags and 'healthy-fats' in replacement_tags:
            is_logical = True
            reasoning.append("Both healthy fats")
        
        # Check price compatibility (within 50% range)
        original_price = original_product['price']
        replacement_price = replacement_product['price']
        price_ratio = replacement_price / original_price
        if 0.5 <= price_ratio <= 2.0:
            reasoning.append("Similar price range")
        else:
            reasoning.append(f"Price difference: {price_ratio:.2f}x")
        
        # Display the analysis
        status = "✅" if is_logical else "❌"
        print(f"{status} {original_product['name']} → {replacement_name}")
        print(f"   Original tags: {', '.join(original_tags)}")
        print(f"   Replacement tags: {', '.join(replacement_tags)}")
        print(f"   Reasoning: {', '.join(reasoning)}")
        print(f"   Price: ${original_price:.2f} → ${replacement_price:.2f}")
        print()
        
        if is_logical:
            valid_replacements += 1
    
    print("=" * 60)
    print(f"📊 Replacement Analysis Summary:")
    print(f"   ✅ Valid replacements: {valid_replacements}")
    print(f"   ❌ Invalid replacements: {total_replacements - valid_replacements}")
    print(f"   📈 Success rate: {(valid_replacements/total_replacements)*100:.1f}%")
    
    if valid_replacements == total_replacements:
        print("🎉 All replacements are logical and relevant!")
    else:
        print("⚠️ Some replacements may need adjustment.")

if __name__ == "__main__":
    verify_replacements() 