from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime, timedelta
import hashlib
import jwt



class Product(BaseModel):
    item_id: str
    name: str
    price: float
    tags: List[str]
    in_stock: bool
    promo: bool
    category: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None

class UserProfile(BaseModel):
    user_id: str
    username: str
    email: str
    name: str
    diet: Optional[str] = None
    allergies: Optional[list] = []
    past_purchases: Optional[list] = []
    budget_limit: Optional[float] = None
    meal_goal: Optional[str] = None
    shopping_frequency: Optional[str] = None
    created_at: Optional[str] = None
    last_login: Optional[str] = None