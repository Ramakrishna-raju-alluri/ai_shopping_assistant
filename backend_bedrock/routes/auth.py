from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime, timedelta
import hashlib
import jwt
from boto3.dynamodb.conditions import Attr

# Reuse bedrock backend dynamo helpers
from backend_bedrock.dynamo.client import dynamodb, USER_TABLE
from backend_bedrock.dynamo.queries import get_user_profile, create_user_profile, update_user_profile


router = APIRouter()

SECRET_KEY = "change-me"  # TODO: env var
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


class UserSignup(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)
    name: str = Field(..., min_length=2, max_length=100)


class UserLogin(BaseModel):
    username: str
    password: str


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
    return hashlib.sha256(password.encode()).hexdigest()


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_user_by_username_or_email(username_or_email: str):
    table = dynamodb.Table(USER_TABLE)
    response = table.scan(FilterExpression=Attr("username").eq(username_or_email))
    items = response.get("Items", [])
    if items:
        return items[0]
    response = table.scan(FilterExpression=Attr("email").eq(username_or_email))
    items = response.get("Items", [])
    if items:
        return items[0]
    return None


async def get_current_user(authorization: str = Header(None)):
    """Extract and validate user from Bearer token with standardized error handling"""
    from backend_bedrock.utils.error_responses import handle_authentication_error
    
    # Check for authorization header
    if not authorization:
        raise handle_authentication_error("Missing authorization header")
    
    # Validate authorization header format
    if not authorization.strip():
        raise handle_authentication_error("Empty authorization header")
    
    try:
        # Parse authorization header
        parts = authorization.strip().split()
        if len(parts) != 2:
            raise handle_authentication_error("Invalid authorization header format. Expected 'Bearer <token>'")
        
        scheme, token = parts
        if scheme.lower() != "bearer":
            raise handle_authentication_error("Invalid authentication scheme. Expected 'Bearer'")
        
        # Validate token is not empty
        if not token.strip():
            raise handle_authentication_error("Empty authentication token")
        
        # Decode and validate JWT token
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        except jwt.ExpiredSignatureError:
            raise handle_authentication_error("Authentication token has expired")
        except jwt.InvalidTokenError:
            raise handle_authentication_error("Invalid authentication token")
        except Exception as e:
            raise handle_authentication_error(f"Token validation failed: {str(e)}")
        
        # Extract user ID from token payload
        user_id: str = payload.get("sub")
        if not user_id:
            raise handle_authentication_error("Missing user ID in authentication token")
        
        # Validate user ID format
        if not isinstance(user_id, str) or not user_id.strip():
            raise handle_authentication_error("Invalid user ID in authentication token")
            
    except Exception as e:
        # If it's already an AuthenticationError, re-raise it
        if hasattr(e, 'status_code') and e.status_code == 401:
            raise e
        # Otherwise, wrap in authentication error
        raise handle_authentication_error(f"Authentication failed: {str(e)}")
    
    # Get user profile from database
    try:
        user = get_user_profile(user_id)
        if not user:
            raise handle_authentication_error("User account not found")
        
        # Ensure user account is active (if we have such a field)
        if user.get("is_active") is False:
            raise handle_authentication_error("User account is deactivated")
            
        return user
        
    except Exception as e:
        # If it's already an AuthenticationError, re-raise it
        if hasattr(e, 'status_code') and e.status_code == 401:
            raise e
        # Otherwise, wrap in authentication error
        raise handle_authentication_error("Failed to retrieve user information")


@router.post("/signup", response_model=UserResponse, status_code=201)
async def signup(user_data: UserSignup):
    from backend_bedrock.utils.error_responses import handle_conflict_error, handle_server_error
    
    try:
        existing_user = get_user_by_username_or_email(user_data.username) or get_user_by_username_or_email(user_data.email)
        if existing_user:
            raise handle_conflict_error("Username or email already registered")

        # Simple sequential ID like backend
        table = dynamodb.Table(USER_TABLE)
        response = table.scan(ProjectionExpression="user_id")
        existing = [i["user_id"] for i in response.get("Items", []) if i.get("user_id", "").startswith("user_")]
        if existing:
            nums = []
            for uid in existing:
                try:
                    nums.append(int(uid.split("_")[1]))
                except Exception:
                    continue
            next_id = f"user_{(max(nums) + 1) if nums else 1}"
        else:
            next_id = "user_1"

        hashed = hash_password(user_data.password)
        now = datetime.utcnow().isoformat()
        profile = {
            "user_id": next_id,
            "username": user_data.username,
            "email": user_data.email,
            "name": user_data.name,
            "password_hash": hashed,
            "created_at": now,
            "last_login": now,
            "diet": "vegetarian",
            "allergies": [],
            "past_purchases": [],
            "budget_limit": 60,
            "meal_goal": "3 meals",
            "shopping_frequency": "weekly",
        }
        create_user_profile(next_id, profile)
        token = create_access_token({"sub": next_id}, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
        return UserResponse(user_id=next_id, username=user_data.username, email=user_data.email, name=user_data.name, access_token=token)
    
    except Exception as e:
        # Re-raise our custom errors
        if hasattr(e, 'status_code'):
            raise e
        raise handle_server_error(f"Failed to create user account: {str(e)}")


@router.post("/login", response_model=UserResponse)
async def login(user_credentials: UserLogin):
    from backend_bedrock.utils.error_responses import handle_authentication_error, handle_server_error
    
    try:
        user = get_user_by_username_or_email(user_credentials.username)
        if not user:
            raise handle_authentication_error("Incorrect username/email or password")
        if hash_password(user_credentials.password) != user.get("password_hash", ""):
            raise handle_authentication_error("Incorrect username/email or password")
        
        user["last_login"] = datetime.utcnow().isoformat()
        update_user_profile(user["user_id"], user)
        token = create_access_token({"sub": user["user_id"]}, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
        return UserResponse(user_id=user["user_id"], username=user["username"], email=user["email"], name=user["name"], access_token=token)
    
    except Exception as e:
        # Re-raise our custom errors
        if hasattr(e, 'status_code'):
            raise e
        raise handle_server_error(f"Login failed: {str(e)}")


@router.get("/profile", response_model=UserProfile)
async def get_profile(current_user: dict = Depends(get_current_user)):
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
        last_login=current_user.get("last_login"),
    )


@router.post("/logout")
async def logout():
    return {"message": "Successfully logged out"}


@router.get("/verify-token")
async def verify_token(current_user: dict = Depends(get_current_user)):
    return {"valid": True, "user_id": current_user["user_id"], "username": current_user["username"]}


