"""
Natural Language Processing utilities for cart management
"""

import re
from typing import Dict, List, Tuple, Any

def parse_quantity_from_text(text: str) -> Dict[str, Any]:
    """
    Parse quantity information from natural language text
    
    Args:
        text: User input text
        
    Returns:
        Dict with parsed quantity information
    """
    text = text.lower().strip()
    
    # Common quantity patterns
    quantity_patterns = [
        # Numbers with units
        (r'(\d+(?:\.\d+)?)\s*(pounds?|lbs?|lb)', 'pounds'),
        (r'(\d+(?:\.\d+)?)\s*(ounces?|oz)', 'ounces'),
        (r'(\d+(?:\.\d+)?)\s*(gallons?|gal)', 'gallons'),
        (r'(\d+(?:\.\d+)?)\s*(liters?|l)', 'liters'),
        (r'(\d+(?:\.\d+)?)\s*(cups?)', 'cups'),
        (r'(\d+(?:\.\d+)?)\s*(bottles?)', 'bottles'),
        (r'(\d+(?:\.\d+)?)\s*(cans?)', 'cans'),
        (r'(\d+(?:\.\d+)?)\s*(boxes?)', 'boxes'),
        (r'(\d+(?:\.\d+)?)\s*(bags?)', 'bags'),
        (r'(\d+(?:\.\d+)?)\s*(packs?)', 'packs'),
        
        # Just numbers
        (r'(\d+(?:\.\d+)?)\s*(?:of\s+)?', 'items'),
        
        # Word numbers
        (r'\b(one|a|an)\b', 'items'),
        (r'\b(two|couple)\b', 'items'),
        (r'\b(three)\b', 'items'),
        (r'\b(four)\b', 'items'),
        (r'\b(five)\b', 'items'),
        (r'\b(six)\b', 'items'),
        (r'\b(dozen)\b', 'items'),
    ]
    
    # Word to number mapping
    word_to_num = {
        'one': 1, 'a': 1, 'an': 1,
        'two': 2, 'couple': 2,
        'three': 3, 'four': 4, 'five': 5, 'six': 6,
        'dozen': 12
    }
    
    for pattern, unit in quantity_patterns:
        match = re.search(pattern, text)
        if match:
            quantity_str = match.group(1)
            
            # Handle word numbers
            if quantity_str in word_to_num:
                quantity = word_to_num[quantity_str]
            else:
                try:
                    quantity = float(quantity_str)
                except (ValueError, IndexError):
                    continue
            
            return {
                "quantity": quantity,
                "unit": unit,
                "raw_match": match.group(0),
                "found": True
            }
    
    # Default quantity if none found
    return {
        "quantity": 1,
        "unit": "items",
        "raw_match": "",
        "found": False
    }

def extract_items_from_batch_request(text: str) -> List[Dict[str, Any]]:
    """
    Extract multiple items from batch requests like "add milk, eggs, and bread"
    
    Args:
        text: User input text
        
    Returns:
        List of items with quantities
    """
    text = text.lower().strip()
    
    # Remove common prefixes
    prefixes_to_remove = [
        r'^(?:add|get|buy|purchase|i need|i want|can you add)\s+',
        r'^(?:to my cart|to cart)\s*',
    ]
    
    for prefix in prefixes_to_remove:
        text = re.sub(prefix, '', text, flags=re.IGNORECASE)
    
    # Split on common separators
    separators = [
        r'\s+and\s+',
        r'\s*,\s*and\s+',
        r'\s*,\s*',
        r'\s*;\s*',
    ]
    
    items = [text]  # Start with full text
    
    for separator in separators:
        new_items = []
        for item in items:
            new_items.extend(re.split(separator, item))
        items = new_items
    
    # Clean and parse each item
    parsed_items = []
    for item in items:
        item = item.strip()
        if not item:
            continue
            
        # Parse quantity for this item
        quantity_info = parse_quantity_from_text(item)
        
        # Extract item name (remove quantity part)
        item_name = item
        if quantity_info["found"] and quantity_info["raw_match"]:
            item_name = item.replace(quantity_info["raw_match"], "").strip()
        
        # Clean up item name
        item_name = re.sub(r'^(?:some|a|an|the)\s+', '', item_name)
        item_name = item_name.strip()
        
        if item_name:
            parsed_items.append({
                "item_name": item_name,
                "quantity": quantity_info["quantity"],
                "unit": quantity_info["unit"],
                "original_text": item
            })
    
    return parsed_items

def normalize_item_name(item_name: str) -> str:
    """
    Normalize item names for better search results
    
    Args:
        item_name: Raw item name
        
    Returns:
        Normalized item name
    """
    # Convert to lowercase
    name = item_name.lower().strip()
    
    # Remove common articles and prepositions
    name = re.sub(r'^(?:a|an|the|some|of)\s+', '', name)
    
    # Handle plurals -> singular for better search
    plural_patterns = [
        (r'ies$', 'y'),      # berries -> berry
        (r'ves$', 'f'),      # loaves -> loaf
        (r'([^s])s$', r'\1'), # apples -> apple (but not grass -> gras)
    ]
    
    for pattern, replacement in plural_patterns:
        name = re.sub(pattern, replacement, name)
    
    # Common substitutions for better search
    substitutions = {
        'veggies': 'vegetables',
        'fruits': 'fruit',
        'bread loaf': 'bread',
        'milk carton': 'milk',
        'soda can': 'soda',
        'beer bottle': 'beer'
    }
    
    for old, new in substitutions.items():
        name = name.replace(old, new)
    
    return name.strip()

def detect_cart_action(text: str) -> Dict[str, Any]:
    """
    Detect what cart action the user wants to perform
    
    Args:
        text: User input text
        
    Returns:
        Dict with detected action and confidence
    """
    text = text.lower().strip()
    
    # Action patterns with confidence scores
    action_patterns = [
        # Add actions
        (r'\b(?:add|put|include|get|buy|purchase|i need|i want)\b.*\b(?:to cart|to my cart|in cart)\b', 'add', 0.9),
        (r'\b(?:add|put|include|get|buy|purchase)\b', 'add', 0.7),
        
        # Remove actions
        (r'\b(?:remove|delete|take out|get rid of)\b.*\b(?:from cart|from my cart)\b', 'remove', 0.9),
        (r'\b(?:remove|delete|take out)\b', 'remove', 0.8),
        
        # View actions
        (r'\b(?:show|display|view|see|check|what\'?s in)\b.*\b(?:cart|my cart)\b', 'view', 0.9),
        (r'\b(?:cart|my cart|shopping cart)\b', 'view', 0.6),
        
        # Clear actions
        (r'\b(?:clear|empty|reset)\b.*\b(?:cart|my cart)\b', 'clear', 0.9),
        
        # Budget actions
        (r'\b(?:budget|spending|cost|total|price)\b', 'budget', 0.7),
        
        # Availability actions
        (r'\b(?:available|in stock|do you have)\b', 'availability', 0.8),
        
        # Substitution actions
        (r'\b(?:substitute|alternative|replace|instead of)\b', 'substitution', 0.8),
    ]
    
    best_action = 'add'  # Default action
    best_confidence = 0.5
    
    for pattern, action, confidence in action_patterns:
        if re.search(pattern, text):
            if confidence > best_confidence:
                best_action = action
                best_confidence = confidence
    
    return {
        "action": best_action,
        "confidence": best_confidence,
        "text": text
    }