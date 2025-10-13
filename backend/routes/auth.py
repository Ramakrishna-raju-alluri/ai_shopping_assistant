from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel, Field, EmailStr
from typing import Optional
import hashlib
import secrets
import string
from datetime import datetime, timedelta
import jwt
from boto3.dynamodb.conditions import Key, Attr

# Import our DynamoDB functions
from dynamo.queries import get_user_profile, create_user_profile, update_user_profile
from dynamo.client import dynamodb, USER_TABLE

router = APIRouter()

# JWT Configuration
SECRET_KEY = "your-secret-key-here"  # In production, use environment variable
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Pydantic models
class UserSignup(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="Username (3-50 characters)")
    email: EmailStr = Field(..., description="Valid email address")
    password: str = Field(..., min_length=6, description="Password (minimum 6 characters)")
    name: str = Field(..., min_length=2, max_length=100, description="Full name")

class UserLogin(BaseModel):
    username: str = Field(..., description="Username or email")
    password: str = Field(..., description="Password")

class UserResponse(BaseModel):
    user_id: str
    username: str
    email: str
    name: str
    access_token: str
    token_type: str = "bearer"

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

def hash_password(password: str) -> str:
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def generate_user_id() -> str:
    """Generate a unique user ID by finding the maximum existing ID and adding +1"""
    table = dynamodb.Table(USER_TABLE)
    
    print(f"🔍 Debug - Starting user ID generation...")
    
    # Get all user_ids using scan with pagination
    existing_ids = []
    last_evaluated_key = None
    
    while True:
        if last_evaluated_key:
            response = table.scan(
                ProjectionExpression="user_id",
                FilterExpression=Attr("user_id").begins_with("user_"),
                ExclusiveStartKey=last_evaluated_key
            )
        else:
            response = table.scan(
                ProjectionExpression="user_id",
                FilterExpression=Attr("user_id").begins_with("user_")
            )
        
        items = response.get("Items", [])
        existing_ids.extend([item["user_id"] for item in items])
        
        last_evaluated_key = response.get("LastEvaluatedKey")
        if not last_evaluated_key:
            break
    
    print(f"🔍 Debug - Found existing user IDs: {existing_ids}")
    
    if not existing_ids:
        print(f"🔍 Debug - No existing users found, returning user_1")
        return "user_1"
    
    # Extract numbers from user_ids and find the highest
    numbers = []
    for user_id in existing_ids:
        try:
            if user_id.startswith("user_"):
                num = int(user_id.split("_")[1])
                numbers.append(num)
        except (IndexError, ValueError):
            continue
    
    print(f"🔍 Debug - Extracted numbers: {numbers}")
    
    if not numbers:
        print(f"🔍 Debug - No valid numbers found, returning user_1")
        return "user_1"
    
    # Find the maximum number and add +1
    max_number = max(numbers)
    next_number = max_number + 1
    
    result = f"user_{next_number}"
    print(f"🔍 Debug - Generated user ID: {result} (max was {max_number})")
    
    return result

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return hash_password(plain_password) == hashed_password

def get_user_by_username_or_email(username_or_email: str):
    """Get user by username or email"""
    table = dynamodb.Table(USER_TABLE)
    
    # Try to find by username first
    response = table.scan(
        FilterExpression=Attr("username").eq(username_or_email)
    )
    items = response.get("Items", [])
    
    if items:
        return items[0]
    
    # If not found by username, try email
    response = table.scan(
        FilterExpression=Attr("email").eq(username_or_email)
    )
    items = response.get("Items", [])
    
    if items:
        return items[0]
    
    return None

async def get_current_user(authorization: str = Header(None)):
    """Get current user from JWT token"""
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if not authorization:
        raise credentials_exception
    
    try:
        # Extract token from "Bearer <token>"
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise credentials_exception
        
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except (ValueError, jwt.PyJWTError):
        raise credentials_exception
    
    user = get_user_profile(user_id)
    if user is None:
        raise credentials_exception
    
    return user

@router.post("/signup", response_model=UserResponse, status_code=201)
async def signup(user_data: UserSignup):
    """User signup endpoint"""
    try:
        # Check if username already exists
        existing_user = get_user_by_username_or_email(user_data.username)
        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="Username already registered"
            )
        
        # Check if email already exists
        existing_user = get_user_by_username_or_email(user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="Email already registered"
            )
        
        # Generate unique user_id
        user_id = generate_user_id()
        print(f"🔍 Debug - Signup: Generated user ID: {user_id}")
        
        # Hash password
        hashed_password = hash_password(user_data.password)
        
        # Create user profile
        user_profile = {
            "user_id": user_id,
            "username": user_data.username,
            "email": user_data.email,
            "name": user_data.name,
            "password_hash": hashed_password,
            "created_at": datetime.utcnow().isoformat(),
            "last_login": datetime.utcnow().isoformat(),
            # Default values for new users
            "diet": "vegetarian",
            "allergies": [],
            "past_purchases": [],
            "budget_limit": 60,
            "meal_goal": "3 meals",
            "shopping_frequency": "weekly"
        }
        
        # Save to DynamoDB
        create_user_profile(user_id, user_profile)
        
        # Create access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user_id}, expires_delta=access_token_expires
        )
        
        return UserResponse(
            user_id=user_id,
            username=user_data.username,
            email=user_data.email,
            name=user_data.name,
            access_token=access_token
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error creating user: {str(e)}"
        )

@router.post("/login", response_model=UserResponse)
async def login(user_credentials: UserLogin):
    """User login endpoint"""
    try:
        # Get user by username or email
        user = get_user_by_username_or_email(user_credentials.username)
        
        if not user:
            raise HTTPException(
                status_code=401,
                detail="Incorrect username/email or password"
            )
        
        # Verify password
        if not verify_password(user_credentials.password, user.get("password_hash", "")):
            raise HTTPException(
                status_code=401,
                detail="Incorrect username/email or password"
            )
        
        # Update last login
        user["last_login"] = datetime.utcnow().isoformat()
        update_user_profile(user["user_id"], user)
        
        # Create access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user["user_id"]}, expires_delta=access_token_expires
        )
        
        return UserResponse(
            user_id=user["user_id"],
            username=user["username"],
            email=user["email"],
            name=user["name"],
            access_token=access_token
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error during login: {str(e)}"
        )

@router.get("/profile", response_model=UserProfile)
async def get_profile(current_user: dict = Depends(get_current_user)):
    """Get current user profile"""
    try:
        return UserProfile(
            user_id=current_user["user_id"],
            username=current_user["username"],
            email=current_user["email"],
            name=current_user["name"],
            diet=current_user.get("diet"),
            allergies=current_user.get("allergies", []),
            past_purchases=current_user.get("past_purchases", []),
            budget_limit=current_user.get("budget_limit"),
            meal_goal=current_user.get("meal_goal"),
            shopping_frequency=current_user.get("shopping_frequency"),
            created_at=current_user.get("created_at"),
            last_login=current_user.get("last_login")
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving profile: {str(e)}"
        )

@router.put("/profile")
async def update_profile(
    profile_update: UserProfile,
    current_user: dict = Depends(get_current_user)
):
    """Update user profile"""
    try:
        from decimal import Decimal
        
        # Update profile data
        updated_profile = current_user.copy()
        updated_profile.update({
            "name": profile_update.name,
            "diet": profile_update.diet,
            "allergies": profile_update.allergies,
            "budget_limit": Decimal(str(profile_update.budget_limit)) if profile_update.budget_limit else None,
            "meal_goal": profile_update.meal_goal,
            "shopping_frequency": profile_update.shopping_frequency
        })
        
        # Save to DynamoDB
        update_user_profile(current_user["user_id"], updated_profile)
        
        return {"message": "Profile updated successfully"}
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error updating profile: {str(e)}"
        )

@router.post("/logout")
async def logout():
    """User logout endpoint (client-side token removal)"""
    return {"message": "Successfully logged out"}

@router.get("/verify-token")
async def verify_token(current_user: dict = Depends(get_current_user)):
    """Verify if current token is valid"""
    return {
        "valid": True,
        "user_id": current_user["user_id"],
        "username": current_user["username"]
    } 