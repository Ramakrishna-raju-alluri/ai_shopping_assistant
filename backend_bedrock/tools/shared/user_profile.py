"""
Shared user profile tools for backend_bedrock.

This module provides centralized user profile management functionality
that can be used by multiple agents across different domains.
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from strands import tool

# Add parent directory to path for imports
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import database functions with flexible import system
try:
    from backend_bedrock.dynamo.queries import get_user_profile as db_get_user_profile
    from backend_bedrock.dynamo.queries import update_user_profile as db_update_user_profile
    from backend_bedrock.dynamo.queries import create_user_profile as db_create_user_profile
except ImportError:
    try:
        from dynamo.queries import get_user_profile as db_get_user_profile
        from dynamo.queries import update_user_profile as db_update_user_profile
        from dynamo.queries import create_user_profile as db_create_user_profile
    except ImportError:
        # Fallback for testing
        def db_get_user_profile(user_id):
            return {"diet": "omnivore", "budget_limit": 100, "allergies": [], "restrictions": []}
        def db_update_user_profile(user_id, profile_data):
            return profile_data
        def db_create_user_profile(user_id, profile_data):
            return profile_data


def convert_decimal_to_float(obj):
    """Convert Decimal objects to float for JSON serialization."""
    import decimal
    if isinstance(obj, decimal.Decimal):
        return float(obj)
    elif isinstance(obj, dict):
        return {k: convert_decimal_to_float(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_decimal_to_float(item) for item in obj]
    return obj


@tool
def fetch_user_profile(user_id: str) -> Dict[str, Any]:
    """
    Fetch user profile data from the database.
    
    Args:
        user_id (str): The user identifier
    
    Returns:
        Dict[str, Any]: Standardized response with user profile data
    """
    try:
        # Direct database call
        user_profile = db_get_user_profile(user_id)
        
        if not user_profile:
            return {
                'success': False,
                'data': None,
                'message': 'User profile not found'
            }
        
        # Convert Decimal objects to float for JSON compatibility
        user_profile = convert_decimal_to_float(user_profile)
        
        # Standardize profile data structure
        profile_data = {
            "user_id": user_id,
            "diet": user_profile.get("diet"),
            "allergies": user_profile.get("allergies", []),
            "restrictions": user_profile.get("restrictions", []),
            "preferred_cuisines": user_profile.get("preferred_cuisines", []),
            "disliked_cuisines": user_profile.get("disliked_cuisines", []),
            "cooking_skill": user_profile.get("cooking_skill"),
            "cooking_time_preference": user_profile.get("cooking_time_preference"),
            "kitchen_equipment": user_profile.get("kitchen_equipment", []),
            "budget_limit": float(user_profile.get("budget_limit", 0)) if user_profile.get("budget_limit") else 0,
            "meal_budget": float(user_profile.get("meal_budget", 0)) if user_profile.get("meal_budget") else None,
            "shopping_frequency": user_profile.get("shopping_frequency"),
            "meal_goal": user_profile.get("meal_goal"),
            "profile_setup_complete": user_profile.get("profile_setup_complete", False),
        }
        
        return {
            'success': True,
            'data': profile_data,
            'message': 'User profile retrieved successfully'
        }
        
    except Exception as e:
        return {
            'success': False,
            'data': None,
            'message': f'Error fetching user profile: {str(e)}'
        }


@tool
def update_user_profile(user_id: str, profile_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update user profile data in the database.
    
    Args:
        user_id (str): The user identifier
        profile_data (Dict[str, Any]): Profile data to update
    
    Returns:
        Dict[str, Any]: Standardized response with updated profile data
    """
    try:
        # Ensure user_id is included in profile data
        profile_data["user_id"] = user_id
        
        # Update profile in database
        updated_profile = db_update_user_profile(user_id, profile_data)
        
        # Convert Decimal objects to float for JSON compatibility
        updated_profile = convert_decimal_to_float(updated_profile)
        
        return {
            'success': True,
            'data': updated_profile,
            'message': 'User profile updated successfully'
        }
        
    except Exception as e:
        return {
            'success': False,
            'data': None,
            'message': f'Error updating user profile: {str(e)}'
        }


@tool
def get_user_preferences(user_id: str) -> Dict[str, Any]:
    """
    Get user dietary preferences and restrictions.
    
    Args:
        user_id (str): The user identifier
    
    Returns:
        Dict[str, Any]: Standardized response with user preferences
    """
    try:
        profile_result = fetch_user_profile(user_id)
        
        if not profile_result['success']:
            return profile_result
        
        profile_data = profile_result['data']
        
        # Extract preference-specific data
        preferences = {
            "diet": profile_data.get("diet"),
            "allergies": profile_data.get("allergies", []),
            "restrictions": profile_data.get("restrictions", []),
            "preferred_cuisines": profile_data.get("preferred_cuisines", []),
            "disliked_cuisines": profile_data.get("disliked_cuisines", []),
            "cooking_skill": profile_data.get("cooking_skill"),
            "cooking_time_preference": profile_data.get("cooking_time_preference"),
            "kitchen_equipment": profile_data.get("kitchen_equipment", []),
        }
        
        return {
            'success': True,
            'data': preferences,
            'message': 'User preferences retrieved successfully'
        }
        
    except Exception as e:
        return {
            'success': False,
            'data': None,
            'message': f'Error fetching user preferences: {str(e)}'
        }


@tool
def get_user_budget_info(user_id: str) -> Dict[str, Any]:
    """
    Get user budget information.
    
    Args:
        user_id (str): The user identifier
    
    Returns:
        Dict[str, Any]: Standardized response with budget information
    """
    try:
        profile_result = fetch_user_profile(user_id)
        
        if not profile_result['success']:
            return profile_result
        
        profile_data = profile_result['data']
        
        # Extract budget-specific data
        budget_info = {
            "budget_limit": profile_data.get("budget_limit", 0),
            "meal_budget": profile_data.get("meal_budget"),
            "shopping_frequency": profile_data.get("shopping_frequency"),
        }
        
        return {
            'success': True,
            'data': budget_info,
            'message': 'User budget information retrieved successfully'
        }
        
    except Exception as e:
        return {
            'success': False,
            'data': None,
            'message': f'Error fetching user budget info: {str(e)}'
        }


@tool
def create_user_profile(user_id: str, profile_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a new user profile.
    
    Args:
        user_id (str): The user identifier
        profile_data (Dict[str, Any]): Initial profile data
    
    Returns:
        Dict[str, Any]: Standardized response with created profile data
    """
    try:
        # Ensure user_id is included in profile data
        profile_data["user_id"] = user_id
        
        # Create profile in database
        created_profile = db_create_user_profile(user_id, profile_data)
        
        # Convert Decimal objects to float for JSON compatibility
        created_profile = convert_decimal_to_float(created_profile)
        
        return {
            'success': True,
            'data': created_profile,
            'message': 'User profile created successfully'
        }
        
    except Exception as e:
        return {
            'success': False,
            'data': None,
            'message': f'Error creating user profile: {str(e)}'
        }


# Legacy compatibility functions for existing code
@tool
def fetch_user_profile_json(user_id: str) -> str:
    """
    Legacy function that returns JSON string for backward compatibility.
    
    Args:
        user_id (str): The user identifier
    
    Returns:
        str: JSON string with user profile data
    """
    result = fetch_user_profile(user_id)
    
    if result['success']:
        return json.dumps(result['data'])
    else:
        return json.dumps({"error": result['message']})

@tool
def get_user_profile_raw(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Legacy function that returns raw profile data for backward compatibility.
    Used by cart operations that expect the old format.
    
    Args:
        user_id (str): The user identifier
    
    Returns:
        Optional[Dict[str, Any]]: Raw profile data or None if not found
    """
    try:
        return db_get_user_profile(user_id)
    except Exception:
        return None