from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from routes.auth import get_current_user
from dynamo.client import dynamodb, USER_TABLE


router = APIRouter()


class DietaryPreferences(BaseModel):
    diet: str = Field(...)
    allergies: List[str] = Field(default=[])
    restrictions: List[str] = Field(default=[])


class CuisinePreferences(BaseModel):
    preferred_cuisines: List[str] = Field(...)
    disliked_cuisines: List[str] = Field(default=[])


class CookingPreferences(BaseModel):
    skill_level: str = Field(...)
    cooking_time_preference: str = Field(...)
    kitchen_equipment: List[str] = Field(default=[])


class BudgetPreferences(BaseModel):
    budget_limit: float = Field(...)
    meal_budget: Optional[float] = Field(None)
    shopping_frequency: str = Field(...)


class CompleteProfileSetup(BaseModel):
    dietary: DietaryPreferences
    cuisine: CuisinePreferences
    cooking: CookingPreferences
    budget: BudgetPreferences
    meal_goal: Optional[str] = Field(None)


@router.get("/status")
async def get_profile_setup_status(current_user: dict = Depends(get_current_user)):
    user_id = current_user.get("user_id")
    try:
        table = dynamodb.Table(USER_TABLE)
        response = table.get_item(Key={"user_id": user_id})
        if "Item" not in response:
            raise HTTPException(status_code=404, detail="User not found")
        user_data = response["Item"]
        missing_sections = []
        if not user_data.get("diet") and not user_data.get("allergies"):
            missing_sections.append("dietary")
        if not user_data.get("preferred_cuisines"):
            missing_sections.append("cuisine")
        if not user_data.get("cooking_skill"):
            missing_sections.append("cooking")
        if not user_data.get("budget_limit"):
            missing_sections.append("budget")
        return {"is_setup_complete": len(missing_sections) == 0, "missing_sections": missing_sections}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking profile status: {str(e)}")


@router.get("/options")
async def get_profile_setup_options():
    return {
        "dietary_options": [
            "vegetarian",
            "vegan",
            "keto",
            "low-carb",
            "gluten-free",
            "high-protein",
            "low-fat",
            "mediterranean",
            "no-restrictions",
            "other",
        ],
        "cuisine_options": [
            "italian",
            "asian",
            "mexican",
            "mediterranean",
            "american",
            "indian",
            "quick_easy",
            "healthy",
        ],
        "cooking_skill_options": ["beginner", "intermediate", "advanced"],
        "cooking_time_options": ["quick", "moderate", "elaborate"],
        "shopping_frequency_options": ["weekly", "bi-weekly", "monthly"],
    }


@router.post("/complete")
async def complete_profile_setup(profile_data: CompleteProfileSetup, current_user: dict = Depends(get_current_user)):
    user_id = current_user.get("user_id")
    try:
        table = dynamodb.Table(USER_TABLE)
        update_data = {
            "diet": profile_data.dietary.diet,
            "allergies": profile_data.dietary.allergies,
            "restrictions": profile_data.dietary.restrictions,
            "preferred_cuisines": profile_data.cuisine.preferred_cuisines,
            "disliked_cuisines": profile_data.cuisine.disliked_cuisines,
            "cooking_skill": profile_data.cooking.skill_level,
            "cooking_time_preference": profile_data.cooking.cooking_time_preference,
            "kitchen_equipment": profile_data.cooking.kitchen_equipment,
            "budget_limit": Decimal(str(profile_data.budget.budget_limit)),
            "meal_budget": Decimal(str(profile_data.budget.meal_budget)) if profile_data.budget.meal_budget else None,
            "shopping_frequency": profile_data.budget.shopping_frequency,
            "meal_goal": profile_data.meal_goal,
            "profile_setup_complete": True,
            "profile_setup_date": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }
        update_expression = "SET "
        expr_names = {}
        expr_values = {}
        for key, value in update_data.items():
            if value is not None:
                update_expression += f"#{key} = :{key}, "
                expr_names[f"#{key}"] = key
                expr_values[f":{key}"] = value
        update_expression = update_expression.rstrip(", ")
        table.update_item(
            Key={"user_id": user_id},
            UpdateExpression=update_expression,
            ExpressionAttributeNames=expr_names,
            ExpressionAttributeValues=expr_values,
            ReturnValues="ALL_NEW",
        )
        return {"message": "Profile setup completed successfully", "user_id": user_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error completing profile setup: {str(e)}")


@router.post("/dietary")
async def update_dietary_preferences(dietary: DietaryPreferences, current_user: dict = Depends(get_current_user)):
    user_id = current_user.get("user_id")
    try:
        table = dynamodb.Table(USER_TABLE)
        table.update_item(
            Key={"user_id": user_id},
            UpdateExpression="SET diet = :diet, allergies = :allergies, restrictions = :restrictions, updated_at = :updated_at",
            ExpressionAttributeValues={
                ":diet": dietary.diet,
                ":allergies": dietary.allergies,
                ":restrictions": dietary.restrictions,
                ":updated_at": datetime.utcnow().isoformat(),
            },
            ReturnValues="ALL_NEW",
        )
        return {"message": "Dietary preferences updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating dietary preferences: {str(e)}")


@router.post("/cuisine")
async def update_cuisine_preferences(cuisine: CuisinePreferences, current_user: dict = Depends(get_current_user)):
    user_id = current_user.get("user_id")
    try:
        table = dynamodb.Table(USER_TABLE)
        table.update_item(
            Key={"user_id": user_id},
            UpdateExpression="SET preferred_cuisines = :preferred, disliked_cuisines = :disliked, updated_at = :updated_at",
            ExpressionAttributeValues={
                ":preferred": cuisine.preferred_cuisines,
                ":disliked": cuisine.disliked_cuisines,
                ":updated_at": datetime.utcnow().isoformat(),
            },
            ReturnValues="ALL_NEW",
        )
        return {"message": "Cuisine preferences updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating cuisine preferences: {str(e)}")


@router.post("/cooking")
async def update_cooking_preferences(cooking: CookingPreferences, current_user: dict = Depends(get_current_user)):
    user_id = current_user.get("user_id")
    try:
        table = dynamodb.Table(USER_TABLE)
        table.update_item(
            Key={"user_id": user_id},
            UpdateExpression="SET cooking_skill = :skill, cooking_time_preference = :time, kitchen_equipment = :equipment, updated_at = :updated_at",
            ExpressionAttributeValues={
                ":skill": cooking.skill_level,
                ":time": cooking.cooking_time_preference,
                ":equipment": cooking.kitchen_equipment,
                ":updated_at": datetime.utcnow().isoformat(),
            },
            ReturnValues="ALL_NEW",
        )
        return {"message": "Cooking preferences updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating cooking preferences: {str(e)}")


@router.post("/budget")
async def update_budget_preferences(budget: BudgetPreferences, current_user: dict = Depends(get_current_user)):
    user_id = current_user.get("user_id")
    try:
        table = dynamodb.Table(USER_TABLE)
        budget_limit = Decimal(str(budget.budget_limit))
        meal_budget = Decimal(str(budget.meal_budget)) if budget.meal_budget else None
        update_expression = "SET budget_limit = :limit, shopping_frequency = :frequency, updated_at = :updated_at"
        expr_values = {":limit": budget_limit, ":frequency": budget.shopping_frequency, ":updated_at": datetime.utcnow().isoformat()}
        if meal_budget:
            update_expression += ", meal_budget = :meal_budget"
            expr_values[":meal_budget"] = meal_budget
        table.update_item(Key={"user_id": user_id}, UpdateExpression=update_expression, ExpressionAttributeValues=expr_values, ReturnValues="ALL_NEW")
        return {"message": "Budget preferences updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating budget preferences: {str(e)}")


@router.get("/user-preferences")
async def get_user_preferences(current_user: dict = Depends(get_current_user)):
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
            "profile_setup_complete": user_data.get("profile_setup_complete", False),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting user preferences: {str(e)}")


