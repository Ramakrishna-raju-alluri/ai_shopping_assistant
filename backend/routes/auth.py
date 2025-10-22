from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime, timedelta
import hashlib
import jwt
from boto3.dynamodb.conditions import Attr

# Reuse bedrock backend dynamo helpers
from dynamo.client import dynamodb, USER_TABLE
from dynamo.queries import get_user_profile, create_user_profile, update_user_profile


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
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")
    else:
        try:
            scheme, token = authorization.split()
            if scheme.lower() != "bearer":
                raise ValueError("Invalid scheme")
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id: str = payload.get("sub")
            if not user_id:
                raise ValueError("Missing subject")
        except Exception:
            raise HTTPException(status_code=401, detail="Could not validate credentials")
        user = get_user_profile(user_id)
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user


@router.post("/signup", response_model=UserResponse, status_code=201)
async def signup(user_data: UserSignup):
    existing_user = get_user_by_username_or_email(user_data.username) or get_user_by_username_or_email(user_data.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Username or email already registered")

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


@router.post("/login", response_model=UserResponse)
async def login(user_credentials: UserLogin):
    user = get_user_by_username_or_email(user_credentials.username)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username/email or password")
    if hash_password(user_credentials.password) != user.get("password_hash", ""):
        raise HTTPException(status_code=401, detail="Incorrect username/email or password")
    user["last_login"] = datetime.utcnow().isoformat()
    update_user_profile(user["user_id"], user)
    token = create_access_token({"sub": user["user_id"]}, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    return UserResponse(user_id=user["user_id"], username=user["username"], email=user["email"], name=user["name"], access_token=token)


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


