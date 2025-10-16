import requests
import sys
from pathlib import Path
from strands import tool
from typing import List, Dict, Any

# Add parent directory to path for imports when running directly
current_dir = Path(__file__).resolve().parent
parent_dir = current_dir.parent
project_root = parent_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import with flexible import system
try:
    from backend_bedrock.api_models import UserProfile, Product
except ImportError:
    try:
        # When running from backend_bedrock directory
        sys.path.insert(0, str(parent_dir))
        from api_models import UserProfile, Product
    except ImportError:
        # Create simple fallback classes if api_models not found
        class UserProfile:
            def __init__(self, **kwargs):
                self.__dict__.update(kwargs)
        class Product:
            def __init__(self, **kwargs):
                self.__dict__.update(kwargs)
                self.price = kwargs.get('price', 0.0)

API_BASE_URL = "http://127.0.0.1:8000/api/v1" # Replace with your actual API URL

@tool
def fetch_user_profile(user_id: str) -> UserProfile:
    """Fetches the user's dietary and budget preferences."""
    # In a real scenario, authentication would be handled

    response = requests.get(f"{API_BASE_URL}/profile/user-preferences")
    response.raise_for_status()
    # Assuming the response JSON directly matches the UserProfile model
    return UserProfile(**response.json())

@tool
def fetch_available_items(category: str = None, in_stock: bool = True) -> List[Product]:
    """Fetches available grocery items from the product catalog."""
    params = {"in_stock": in_stock}
    if category:
        params["category"] = category
    response = requests.get(f"{API_BASE_URL}/products", params=params)
    response.raise_for_status()
    # Assuming the response contains a 'products' key with a list of items
    products_data = response.json().get("products", [])
    print(p in products_data)
    return [Product(**p) for p in products_data]

@tool
def calculate_calories(ingredients: List[str]) -> int:
    """Calculates the estimated total calories for a list of ingredients."""
    # Placeholder for calorie calculation logic or API call
    return len(ingredients) * 150

@tool
def calculate_cost(items: List[Product]) -> float:
    """Calculates the total cost of a list of grocery items."""
    print(items)
    return sum(item.price for item in items)