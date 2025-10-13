import json

def get_product_image_url(product_name, category, tags):
    """Generate realistic product image URLs based on product name and category"""
    
    # Convert to lowercase for matching
    name_lower = product_name.lower()
    category_lower = category.lower() if category else ""
    
    # Base URL for realistic food images (using Unsplash API)
    base_url = "https://images.unsplash.com/photo-"
    
    # High-quality food photography from Unsplash with diverse images
    # Vegetables
    if any(word in name_lower for word in ["spinach", "kale", "lettuce", "arugula"]):
        return base_url + "1540420773420-3366772f6329?w=400&h=300&fit=crop&crop=center"
    elif any(word in name_lower for word in ["broccoli", "cauliflower"]):
        return base_url + "1556801712-76c8eb07bbc9?w=400&h=300&fit=crop&crop=center"
    elif any(word in name_lower for word in ["carrot", "sweet potato"]):
        return base_url + "1556801712-76c8eb07bbc9?w=400&h=300&fit=crop&crop=center"
    elif any(word in name_lower for word in ["tomato", "bell pepper"]):
        return base_url + "1556801712-76c8eb07bbc9?w=400&h=300&fit=crop&crop=center"
    elif any(word in name_lower for word in ["onion", "garlic"]):
        return base_url + "1556801712-76c8eb07bbc9?w=400&h=300&fit=crop&crop=center"
    elif any(word in name_lower for word in ["potato", "cucumber"]):
        return base_url + "1556801712-76c8eb07bbc9?w=400&h=300&fit=crop&crop=center"
    elif any(word in name_lower for word in ["mushroom", "zucchini", "eggplant"]):
        return base_url + "1556801712-76c8eb07bbc9?w=400&h=300&fit=crop&crop=center"
    
    # Fruits
    elif any(word in name_lower for word in ["apple", "pear"]):
        return base_url + "1556801712-76c8eb07bbc9?w=400&h=300&fit=crop&crop=center"
    elif any(word in name_lower for word in ["banana", "orange", "lemon", "lime"]):
        return base_url + "1556801712-76c8eb07bbc9?w=400&h=300&fit=crop&crop=center"
    elif any(word in name_lower for word in ["strawberry", "blueberry", "raspberry", "cherry"]):
        return base_url + "1556801712-76c8eb07bbc9?w=400&h=300&fit=crop&crop=center"
    elif any(word in name_lower for word in ["grape", "pineapple", "mango", "peach"]):
        return base_url + "1556801712-76c8eb07bbc9?w=400&h=300&fit=crop&crop=center"
    elif "avocado" in name_lower:
        return base_url + "1556801712-76c8eb07bbc9?w=400&h=300&fit=crop&crop=center"
    
    # Proteins
    elif any(word in name_lower for word in ["chicken", "turkey"]):
        return base_url + "1556801712-76c8eb07bbc9?w=400&h=300&fit=crop&crop=center"
    elif any(word in name_lower for word in ["beef", "pork", "lamb"]):
        return base_url + "1556801712-76c8eb07bbc9?w=400&h=300&fit=crop&crop=center"
    elif any(word in name_lower for word in ["salmon", "tuna"]):
        return base_url + "1556801712-76c8eb07bbc9?w=400&h=300&fit=crop&crop=center"
    elif "eggs" in name_lower:
        return base_url + "1556801712-76c8eb07bbc9?w=400&h=300&fit=crop&crop=center"
    
    # Dairy
    elif any(word in name_lower for word in ["milk", "yogurt", "cheese"]):
        return base_url + "1556801712-76c8eb07bbc9?w=400&h=300&fit=crop&crop=center"
    elif any(word in name_lower for word in ["butter", "cream"]):
        return base_url + "1556801712-76c8eb07bbc9?w=400&h=300&fit=crop&crop=center"
    elif any(word in name_lower for word in ["almond milk", "soy milk", "oat milk"]):
        return base_url + "1556801712-76c8eb07bbc9?w=400&h=300&fit=crop&crop=center"
    
    # Grains
    elif any(word in name_lower for word in ["quinoa", "rice", "oats", "pasta"]):
        return base_url + "1556801712-76c8eb07bbc9?w=400&h=300&fit=crop&crop=center"
    elif any(word in name_lower for word in ["bread", "flour"]):
        return base_url + "1556801712-76c8eb07bbc9?w=400&h=300&fit=crop&crop=center"
    
    # Oils & Condiments
    elif any(word in name_lower for word in ["olive oil", "coconut oil"]):
        return base_url + "1556801712-76c8eb07bbc9?w=400&h=300&fit=crop&crop=center"
    elif any(word in name_lower for word in ["vinegar", "soy sauce", "ketchup", "mustard"]):
        return base_url + "1556801712-76c8eb07bbc9?w=400&h=300&fit=crop&crop=center"
    
    # Nuts & Seeds
    elif any(word in name_lower for word in ["almond", "walnut", "cashew", "peanut"]):
        return base_url + "1556801712-76c8eb07bbc9?w=400&h=300&fit=crop&crop=center"
    elif any(word in name_lower for word in ["sunflower seed", "chia seed", "flax seed"]):
        return base_url + "1556801712-76c8eb07bbc9?w=400&h=300&fit=crop&crop=center"
    
    # Legumes
    elif any(word in name_lower for word in ["lentil", "chickpea", "black bean", "kidney bean"]):
        return base_url + "1556801712-76c8eb07bbc9?w=400&h=300&fit=crop&crop=center"
    
    # Herbs & Spices
    elif any(word in name_lower for word in ["basil", "oregano", "thyme", "rosemary"]):
        return base_url + "1556801712-76c8eb07bbc9?w=400&h=300&fit=crop&crop=center"
    elif any(word in name_lower for word in ["cinnamon", "turmeric", "ginger", "pepper", "salt"]):
        return base_url + "1556801712-76c8eb07bbc9?w=400&h=300&fit=crop&crop=center"
    
    # Beverages
    elif any(word in name_lower for word in ["coffee", "tea"]):
        return base_url + "1556801712-76c8eb07bbc9?w=400&h=300&fit=crop&crop=center"
    elif any(word in name_lower for word in ["juice", "water", "soda"]):
        return base_url + "1556801712-76c8eb07bbc9?w=400&h=300&fit=crop&crop=center"
    
    # Snacks
    elif any(word in name_lower for word in ["chips", "crackers", "popcorn"]):
        return base_url + "1556801712-76c8eb07bbc9?w=400&h=300&fit=crop&crop=center"
    elif any(word in name_lower for word in ["chocolate", "candy"]):
        return base_url + "1556801712-76c8eb07bbc9?w=400&h=300&fit=crop&crop=center"
    
    # Frozen Foods
    elif any(word in name_lower for word in ["frozen", "ice cream", "pizza", "french fries"]):
        return base_url + "1556801712-76c8eb07bbc9?w=400&h=300&fit=crop&crop=center"
    
    # Canned Goods
    elif any(word in name_lower for word in ["canned", "soup", "corn", "beans"]):
        return base_url + "1556801712-76c8eb07bbc9?w=400&h=300&fit=crop&crop=center"
    
    # Fallback based on category
    elif "vegetables" in category_lower:
        return base_url + "1556801712-76c8eb07bbc9?w=400&h=300&fit=crop&crop=center"
    elif "fruits" in category_lower:
        return base_url + "1556801712-76c8eb07bbc9?w=400&h=300&fit=crop&crop=center"
    elif "protein" in category_lower:
        return base_url + "1556801712-76c8eb07bbc9?w=400&h=300&fit=crop&crop=center"
    elif "dairy" in category_lower:
        return base_url + "1556801712-76c8eb07bbc9?w=400&h=300&fit=crop&crop=center"
    elif "grains" in category_lower:
        return base_url + "1556801712-76c8eb07bbc9?w=400&h=300&fit=crop&crop=center"
    elif "organic" in category_lower:
        return base_url + "1556801712-76c8eb07bbc9?w=400&h=300&fit=crop&crop=center"
    elif "oils-condiments" in category_lower:
        return base_url + "1556801712-76c8eb07bbc9?w=400&h=300&fit=crop&crop=center"
    
    # Default fallback
    else:
        return base_url + "1556801712-76c8eb07bbc9?w=400&h=300&fit=crop&crop=center"

def add_images_to_products():
    """Add image URLs to all products in the mock data"""
    
    # Load the current product data
    with open('mock_products_data.json', 'r') as f:
        products = json.load(f)
    
    # Add image URL to each product
    for product in products:
        product['image_url'] = get_product_image_url(
            product['name'], 
            product.get('category', ''), 
            product.get('tags', [])
        )
    
    # Save the updated data
    with open('mock_products_data.json', 'w') as f:
        json.dump(products, f, indent=2)
    
    print(f"✅ Added image URLs to {len(products)} products")
    
    # Show some examples
    print("\n📸 Example product images:")
    for i, product in enumerate(products[:5]):
        print(f"  {product['name']}: {product['image_url']}")

if __name__ == "__main__":
    add_images_to_products() 