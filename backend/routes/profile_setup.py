#!/usr/bin/env python3
"""
User Profile Setup and Preferences Management
Handles new user onboarding and profile updates
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
import boto3
from boto3.dynamodb.conditions import Key, Attr
from routes.auth import get_current_user
from dynamo.client import dynamodb, USER_TABLE

router = APIRouter(prefix="/profile-setup", tags=["Profile Setup"])

# Pydantic models for profile setup
class DietaryPreferences(BaseModel):
    diet: str = Field(..., description="Dietary preference (vegetarian, vegan, keto, etc.)")
    allergies: List[str] = Field(default=[], description="List of food allergies")
    restrictions: List[str] = Field(default=[], description="Other dietary restrictions")

class CuisinePreferences(BaseModel):
    preferred_cuisines: List[str] = Field(..., description="List of preferred cuisines")
    disliked_cuisines: List[str] = Field(default=[], description="List of disliked cuisines")

class CookingPreferences(BaseModel):
    skill_level: str = Field(..., description="Cooking skill level (beginner, intermediate, advanced)")
    cooking_time_preference: str = Field(..., description="Preferred cooking time (quick, moderate, elaborate)")
    kitchen_equipment: List[str] = Field(default=[], description="Available kitchen equipment")

class BudgetPreferences(BaseModel):
    budget_limit: float = Field(..., description="Monthly budget limit")
    meal_budget: Optional[float] = Field(None, description="Per-meal budget limit")
    shopping_frequency: str = Field(..., description="Shopping frequency (weekly, bi-weekly, monthly)")

class CompleteProfileSetup(BaseModel):
    dietary: DietaryPreferences
    cuisine: CuisinePreferences
    cooking: CookingPreferences
    budget: BudgetPreferences
    meal_goal: Optional[str] = Field(None, description="Meal planning goal")

class ProfileStatus(BaseModel):
    is_setup_complete: bool
    missing_sections: List[str]
    profile_data: dict

# Available options for profile setup
DIETARY_OPTIONS = [
    "vegetarian", "vegan", "keto", "low-carb", "gluten-free", 
    "high-protein", "low-fat", "mediterranean", "no-restrictions", "other"
]

CUISINE_OPTIONS = [
    "italian", "asian", "mexican", "mediterranean", "american", 
    "indian", "quick_easy", "healthy"
]

COOKING_SKILL_OPTIONS = ["beginner", "intermediate", "advanced"]
COOKING_TIME_OPTIONS = ["quick", "moderate", "elaborate"]
SHOPPING_FREQUENCY_OPTIONS = ["weekly", "bi-weekly", "monthly"]

def convert_floats_to_decimals(data):
    """Convert float values to Decimal for DynamoDB compatibility"""
    if isinstance(data, dict):
        return {k: convert_floats_to_decimals(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [convert_floats_to_decimals(item) for item in data]
    elif isinstance(data, float):
        return Decimal(str(data))
    else:
        return data

@router.get("/status", response_model=ProfileStatus)
async def get_profile_setup_status(current_user: dict = Depends(get_current_user)):
    """Check if user profile setup is complete and what's missing"""
    user_id = current_user.get("user_id")
    
    try:
        table = dynamodb.Table(USER_TABLE)
        response = table.get_item(Key={"user_id": user_id})
        
        if "Item" not in response:
            raise HTTPException(status_code=404, detail="User not found")
        
        user_data = response["Item"]
        
        # Check what sections are complete
        missing_sections = []
        profile_data = {}
        
        # Check dietary preferences
        if not user_data.get("diet") and not user_data.get("allergies"):
            missing_sections.append("dietary")
        else:
            profile_data["dietary"] = {
                "diet": user_data.get("diet"),
                "allergies": user_data.get("allergies", [])
            }
        
        # Check cuisine preferences
        if not user_data.get("preferred_cuisines"):
            missing_sections.append("cuisine")
        else:
            profile_data["cuisine"] = {
                "preferred_cuisines": user_data.get("preferred_cuisines", []),
                "disliked_cuisines": user_data.get("disliked_cuisines", [])
            }
        
        # Check cooking preferences
        if not user_data.get("cooking_skill"):
            missing_sections.append("cooking")
        else:
            profile_data["cooking"] = {
                "skill_level": user_data.get("cooking_skill"),
                "cooking_time_preference": user_data.get("cooking_time_preference"),
                "kitchen_equipment": user_data.get("kitchen_equipment", [])
            }
        
        # Check budget preferences
        if not user_data.get("budget_limit"):
            missing_sections.append("budget")
        else:
            profile_data["budget"] = {
                "budget_limit": float(user_data.get("budget_limit", 0)),
                "meal_budget": float(user_data.get("meal_budget", 0)) if user_data.get("meal_budget") else None,
                "shopping_frequency": user_data.get("shopping_frequency")
            }
        
        is_setup_complete = len(missing_sections) == 0
        
        return ProfileStatus(
            is_setup_complete=is_setup_complete,
            missing_sections=missing_sections,
            profile_data=profile_data
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking profile status: {str(e)}")

@router.get("/options")
async def get_profile_setup_options():
    """Get available options for profile setup"""
    return {
        "dietary_options": DIETARY_OPTIONS,
        "cuisine_options": CUISINE_OPTIONS,
        "cooking_skill_options": COOKING_SKILL_OPTIONS,
        "cooking_time_options": COOKING_TIME_OPTIONS,
        "shopping_frequency_options": SHOPPING_FREQUENCY_OPTIONS
    }

@router.post("/complete")
async def complete_profile_setup(
    profile_data: CompleteProfileSetup,
    current_user: dict = Depends(get_current_user)
):
    """Complete the full profile setup for a new user"""
    user_id = current_user.get("user_id")
    
    try:
        table = dynamodb.Table(USER_TABLE)
        
        # Prepare update data with Decimal conversion
        update_data = {
            # Dietary preferences
            "diet": profile_data.dietary.diet,
            "allergies": profile_data.dietary.allergies,
            "restrictions": profile_data.dietary.restrictions,
            
            # Cuisine preferences
            "preferred_cuisines": profile_data.cuisine.preferred_cuisines,
            "disliked_cuisines": profile_data.cuisine.disliked_cuisines,
            
            # Cooking preferences
            "cooking_skill": profile_data.cooking.skill_level,
            "cooking_time_preference": profile_data.cooking.cooking_time_preference,
            "kitchen_equipment": profile_data.cooking.kitchen_equipment,
            
            # Budget preferences (convert to Decimal)
            "budget_limit": Decimal(str(profile_data.budget.budget_limit)),
            "meal_budget": Decimal(str(profile_data.budget.meal_budget)) if profile_data.budget.meal_budget else None,
            "shopping_frequency": profile_data.budget.shopping_frequency,
            
            # Additional preferences
            "meal_goal": profile_data.meal_goal,
            
            # Metadata
            "profile_setup_complete": True,
            "profile_setup_date": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        # Build update expression
        update_expression = "SET "
        expression_values = {}
        
        for key, value in update_data.items():
            if value is not None:
                update_expression += f"#{key} = :{key}, "
                expression_values[f":{key}"] = value
        
        # Remove trailing comma and space
        update_expression = update_expression.rstrip(", ")
        
        # Create attribute names mapping
        expression_names = {f"#{key}": key for key in update_data.keys() if update_data[key] is not None}
        
        # Update the user record
        response = table.update_item(
            Key={"user_id": user_id},
            UpdateExpression=update_expression,
            ExpressionAttributeNames=expression_names,
            ExpressionAttributeValues=expression_values,
            ReturnValues="ALL_NEW"
        )
        
        return {
            "message": "Profile setup completed successfully",
            "user_id": user_id,
            "profile_data": response.get("Attributes", {})
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error completing profile setup: {str(e)}")

@router.post("/dietary")
async def update_dietary_preferences(
    dietary: DietaryPreferences,
    current_user: dict = Depends(get_current_user)
):
    """Update dietary preferences"""
    user_id = current_user.get("user_id")
    
    try:
        table = dynamodb.Table(USER_TABLE)
        
        response = table.update_item(
            Key={"user_id": user_id},
            UpdateExpression="SET diet = :diet, allergies = :allergies, restrictions = :restrictions, updated_at = :updated_at",
            ExpressionAttributeValues={
                ":diet": dietary.diet,
                ":allergies": dietary.allergies,
                ":restrictions": dietary.restrictions,
                ":updated_at": datetime.utcnow().isoformat()
            },
            ReturnValues="ALL_NEW"
        )
        
        return {
            "message": "Dietary preferences updated successfully",
            "dietary_data": {
                "diet": dietary.diet,
                "allergies": dietary.allergies,
                "restrictions": dietary.restrictions
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating dietary preferences: {str(e)}")

@router.post("/cuisine")
async def update_cuisine_preferences(
    cuisine: CuisinePreferences,
    current_user: dict = Depends(get_current_user)
):
    """Update cuisine preferences"""
    user_id = current_user.get("user_id")
    
    try:
        table = dynamodb.Table(USER_TABLE)
        
        response = table.update_item(
            Key={"user_id": user_id},
            UpdateExpression="SET preferred_cuisines = :preferred, disliked_cuisines = :disliked, updated_at = :updated_at",
            ExpressionAttributeValues={
                ":preferred": cuisine.preferred_cuisines,
                ":disliked": cuisine.disliked_cuisines,
                ":updated_at": datetime.utcnow().isoformat()
            },
            ReturnValues="ALL_NEW"
        )
        
        return {
            "message": "Cuisine preferences updated successfully",
            "cuisine_data": {
                "preferred_cuisines": cuisine.preferred_cuisines,
                "disliked_cuisines": cuisine.disliked_cuisines
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating cuisine preferences: {str(e)}")

@router.post("/cooking")
async def update_cooking_preferences(
    cooking: CookingPreferences,
    current_user: dict = Depends(get_current_user)
):
    """Update cooking preferences"""
    user_id = current_user.get("user_id")
    
    try:
        table = dynamodb.Table(USER_TABLE)
        
        response = table.update_item(
            Key={"user_id": user_id},
            UpdateExpression="SET cooking_skill = :skill, cooking_time_preference = :time, kitchen_equipment = :equipment, updated_at = :updated_at",
            ExpressionAttributeValues={
                ":skill": cooking.skill_level,
                ":time": cooking.cooking_time_preference,
                ":equipment": cooking.kitchen_equipment,
                ":updated_at": datetime.utcnow().isoformat()
            },
            ReturnValues="ALL_NEW"
        )
        
        return {
            "message": "Cooking preferences updated successfully",
            "cooking_data": {
                "skill_level": cooking.skill_level,
                "cooking_time_preference": cooking.cooking_time_preference,
                "kitchen_equipment": cooking.kitchen_equipment
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating cooking preferences: {str(e)}")

@router.post("/budget")
async def update_budget_preferences(
    budget: BudgetPreferences,
    current_user: dict = Depends(get_current_user)
):
    """Update budget preferences"""
    user_id = current_user.get("user_id")
    
    try:
        table = dynamodb.Table(USER_TABLE)
        
        # Convert floats to Decimal for DynamoDB
        budget_limit = Decimal(str(budget.budget_limit))
        meal_budget = Decimal(str(budget.meal_budget)) if budget.meal_budget else None
        
        update_expression = "SET budget_limit = :limit, shopping_frequency = :frequency, updated_at = :updated_at"
        expression_values = {
            ":limit": budget_limit,
            ":frequency": budget.shopping_frequency,
            ":updated_at": datetime.utcnow().isoformat()
        }
        
        if meal_budget:
            update_expression += ", meal_budget = :meal_budget"
            expression_values[":meal_budget"] = meal_budget
        
        response = table.update_item(
            Key={"user_id": user_id},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_values,
            ReturnValues="ALL_NEW"
        )
        
        return {
            "message": "Budget preferences updated successfully",
            "budget_data": {
                "budget_limit": float(budget_limit),
                "meal_budget": float(meal_budget) if meal_budget else None,
                "shopping_frequency": budget.shopping_frequency
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating budget preferences: {str(e)}")

@router.get("/user-preferences")
async def get_user_preferences(current_user: dict = Depends(get_current_user)):
    """Get complete user preferences for meal planning"""
    user_id = current_user.get("user_id")
    
    try:
        table = dynamodb.Table(USER_TABLE)
        response = table.get_item(Key={"user_id": user_id})
        
        if "Item" not in response:
            raise HTTPException(status_code=404, detail="User not found")
        
        user_data = response["Item"]
        
        return {
            "user_id": user_id,
            "diet": user_data.get("diet"),
            "allergies": user_data.get("allergies", []),
            "restrictions": user_data.get("restrictions", []),
            "preferred_cuisines": user_data.get("preferred_cuisines", []),
            "disliked_cuisines": user_data.get("disliked_cuisines", []),
            "cooking_skill": user_data.get("cooking_skill"),
            "cooking_time_preference": user_data.get("cooking_time_preference"),
            "kitchen_equipment": user_data.get("kitchen_equipment", []),
            "budget_limit": float(user_data.get("budget_limit", 0)),
            "meal_budget": float(user_data.get("meal_budget", 0)) if user_data.get("meal_budget") else None,
            "shopping_frequency": user_data.get("shopping_frequency"),
            "meal_goal": user_data.get("meal_goal"),
            "profile_setup_complete": user_data.get("profile_setup_complete", False)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting user preferences: {str(e)}") 