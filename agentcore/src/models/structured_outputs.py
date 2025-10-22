"""
Pydantic models for structured agent outputs.

This module defines the structured output models used by the multi-agent grocery assistant system
to return formatted data instead of plain text responses. Models follow the pattern from temp.py
with proper Field descriptions and validation constraints.
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date


class HealthSummary(BaseModel):
    """Structured health and nutrition summary data."""
    
    date: str = Field(description="Date in YYYY-MM-DD format")
    total_calories: float = Field(description="Total calories consumed for the day")
    target_calories: float = Field(description="Daily calorie target")
    remaining_calories: float = Field(description="Calories remaining to reach target")
    protein: float = Field(description="Total protein in grams")
    carbs: float = Field(description="Total carbohydrates in grams")
    fat: float = Field(description="Total fat in grams")
    meals: List[str] = Field(description="List of meals consumed")
    recommendations: List[str] = Field(description="Health recommendations")
    health_score: int = Field(ge=1, le=10, description="Daily health score from 1-10")


class CartItem(BaseModel):
    """Individual item in a grocery cart."""
    
    name: str = Field(description="Product name")
    quantity: int = Field(description="Quantity in cart")
    price: float = Field(description="Price per unit")
    total_price: float = Field(description="Total price for quantity")
    availability: str = Field(description="In stock, out of stock, or limited")


class GrocerySummary(BaseModel):
    """Structured grocery cart and shopping summary data."""
    
    cart_items: List[CartItem] = Field(description="Items currently in cart")
    total_cost: float = Field(description="Total cart cost")
    item_count: int = Field(description="Total number of items")
    budget_set: Optional[float] = Field(description="User's set budget amount")
    budget_remaining: Optional[float] = Field(description="Remaining budget if set")
    budget_status: str = Field(description="Budget status: within_budget, over_budget, or no_budget_set")
    savings_opportunities: List[str] = Field(description="Ways to save money on current cart")
    recommendations: List[str] = Field(description="Shopping recommendations")
    substitutions: List[str] = Field(description="Suggested product substitutions")
    availability_summary: str = Field(description="Overall availability status of cart items")


class Recipe(BaseModel):
    """Individual recipe with detailed information."""
    
    name: str = Field(description="Recipe name")
    prep_time: int = Field(description="Preparation time in minutes")
    cook_time: int = Field(description="Cooking time in minutes")
    servings: int = Field(description="Number of servings")
    ingredients: List[str] = Field(description="List of ingredients with quantities")
    instructions: List[str] = Field(description="Step-by-step cooking instructions")
    calories_per_serving: float = Field(description="Calories per serving")
    dietary_tags: List[str] = Field(description="Dietary tags like vegetarian, gluten-free, etc.")
    difficulty_level: str = Field(description="Easy, Medium, or Hard")
    meal_type: str = Field(description="Breakfast, Lunch, Dinner, or Snack")


class MealPlan(BaseModel):
    """Structured meal planning data with recipes and nutrition information."""
    
    date: str = Field(description="Date for meal plan in YYYY-MM-DD format")
    recipes: List[Recipe] = Field(description="Planned recipes for the day")
    total_calories: float = Field(description="Total calories for all meals")
    total_prep_time: int = Field(description="Total preparation time in minutes")
    total_cook_time: int = Field(description="Total cooking time in minutes")
    shopping_list: List[str] = Field(description="Generated shopping list with quantities")
    ingredient_substitutions: List[str] = Field(description="Suggested ingredient substitutions")
    dietary_notes: List[str] = Field(description="Dietary restriction and preference notes")
    nutritional_summary: dict = Field(description="Summary of total protein, carbs, fat, etc.")
    meal_balance_score: int = Field(ge=1, le=10, description="Nutritional balance score from 1-10")
    estimated_cost: Optional[float] = Field(description="Estimated total cost for ingredients")