from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel, EmailStr
from typing import Optional
from sqlalchemy import select

from app.database.connection import AsyncSessionLocal
from app.database.models import DBUser
from app.auth.security import hash_password, verify_password, create_access_token, decode_access_token

router = APIRouter(prefix="/api/auth", tags=["Authentication & User Profile"])

class UserRegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str

class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str

class ProfileUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    avatar_url: Optional[str] = None

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str

async def get_current_user_from_header(authorization: Optional[str] = Header(None)) -> DBUser:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authentication token missing or invalid")
    
    token = authorization.split(" ")[1]
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=401, detail="Session expired or invalid token")
    
    user_id = int(payload["sub"])
    async with AsyncSessionLocal() as session:
        stmt = select(DBUser).where(DBUser.id == user_id)
        res = await session.execute(stmt)
        user = res.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=401, detail="User account not found")
        return user

@router.post("/register")
async def register(req: UserRegisterRequest):
    """Registers a new user account."""
    if len(req.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    
    async with AsyncSessionLocal() as session:
        # Check existing user
        stmt = select(DBUser).where(DBUser.email == req.email.lower())
        res = await session.execute(stmt)
        existing = res.scalar_one_or_none()
        if existing:
            raise HTTPException(status_code=400, detail="An account with this email already exists")
        
        # Default avatar
        initials = "".join([part[0].upper() for part in req.full_name.split()[:2]]) or "U"
        avatar = f"https://ui-avatars.com/api/?name={initials}&background=2563eb&color=fff"
        
        new_user = DBUser(
            email=req.email.lower(),
            full_name=req.full_name,
            hashed_password=hash_password(req.password),
            avatar_url=avatar,
            plan_tier="PRO"
        )
        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)
        
        token = create_access_token({"sub": str(new_user.id), "email": new_user.email})
        
        return {
            "token": token,
            "user": {
                "id": new_user.id,
                "email": new_user.email,
                "full_name": new_user.full_name,
                "plan_tier": new_user.plan_tier,
                "avatar_url": new_user.avatar_url
            }
        }

@router.post("/login")
async def login(req: UserLoginRequest):
    """Authenticates existing user with email and password."""
    async with AsyncSessionLocal() as session:
        stmt = select(DBUser).where(DBUser.email == req.email.lower())
        res = await session.execute(stmt)
        user = res.scalar_one_or_none()
        
        if not user or not verify_password(req.password, user.hashed_password):
            raise HTTPException(status_code=400, detail="Invalid email or password")
        
        token = create_access_token({"sub": str(user.id), "email": user.email})
        
        return {
            "token": token,
            "user": {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "plan_tier": user.plan_tier,
                "avatar_url": user.avatar_url
            }
        }

@router.get("/me")
async def get_me(user: DBUser = Depends(get_current_user_from_header)):
    """Fetches profile info for currently logged-in user."""
    return {
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "plan_tier": user.plan_tier,
            "avatar_url": user.avatar_url,
            "created_at": str(user.created_at)
        }
    }

@router.put("/profile")
async def update_profile(
    req: ProfileUpdateRequest,
    current_user: DBUser = Depends(get_current_user_from_header)
):
    """Updates user profile information."""
    async with AsyncSessionLocal() as session:
        stmt = select(DBUser).where(DBUser.id == current_user.id)
        res = await session.execute(stmt)
        user = res.scalar_one()
        
        if req.full_name:
            user.full_name = req.full_name
        if req.email:
            user.email = req.email.lower()
        if req.avatar_url:
            user.avatar_url = req.avatar_url
            
        await session.commit()
        await session.refresh(user)
        
        return {
            "user": {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "plan_tier": user.plan_tier,
                "avatar_url": user.avatar_url
            }
        }

@router.put("/change-password")
async def change_password(
    req: ChangePasswordRequest,
    current_user: DBUser = Depends(get_current_user_from_header)
):
    """Changes password for logged in user."""
    async with AsyncSessionLocal() as session:
        stmt = select(DBUser).where(DBUser.id == current_user.id)
        res = await session.execute(stmt)
        user = res.scalar_one()
        
        if not verify_password(req.old_password, user.hashed_password):
            raise HTTPException(status_code=400, detail="Incorrect existing password")
            
        if len(req.new_password) < 6:
            raise HTTPException(status_code=400, detail="New password must be at least 6 characters")
            
        user.hashed_password = hash_password(req.new_password)
        await session.commit()
        
        return {"status": "success", "message": "Password changed successfully"}
