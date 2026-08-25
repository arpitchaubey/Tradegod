from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel, EmailStr
from typing import Optional
from sqlalchemy import select
import secrets
import time
import logging

from app.database.connection import AsyncSessionLocal
from app.database.models import DBUser
from app.auth.security import hash_password, verify_password, create_access_token, decode_access_token
from app.auth.email import email_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["Authentication & User Profile"])

# In-memory store for reset verification codes: email -> {"code": str, "expires_at": float, "attempts": int, "requests": list[float]}
_RESET_CODES: dict[str, dict] = {}

class UserRegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str

class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    email: EmailStr
    reset_code: str
    new_password: str

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

@router.post("/forgot-password")
async def forgot_password(req: ForgotPasswordRequest):
    """Generates a secure 6-digit password reset code and dispatches it to the user's email."""
    normalized_email = req.email.lower().strip()
    async with AsyncSessionLocal() as session:
        stmt = select(DBUser).where(DBUser.email == normalized_email)
        res = await session.execute(stmt)
        user = res.scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=404, detail="No account registered with this email address")
        
        now = time.time()
        existing_record = _RESET_CODES.get(normalized_email, {})
        request_history = [t for t in existing_record.get("requests", []) if now - t < 900]
        
        # Rate limit: max 5 reset requests per 15 minutes
        if len(request_history) >= 5:
            raise HTTPException(
                status_code=429, 
                detail="Too many password reset requests. Please wait a few minutes before trying again."
            )
        
        request_history.append(now)

        # Generate 6-digit numeric reset code
        code = "".join([str(secrets.randbelow(10)) for _ in range(6)])
        
        # Valid for 15 minutes, with brute-force attempt counter
        _RESET_CODES[normalized_email] = {
            "code": code,
            "expires_at": now + 900,
            "attempts": 0,
            "requests": request_history
        }
        
        logger.info(f"Password reset requested for {normalized_email}. Dispatching verification email.")
        
        # Send OTP code asynchronously via email
        await email_service.send_password_reset_otp(normalized_email, code)
        
        # SECURE RESPONSE: Never expose the OTP code to the client
        return {
            "status": "success",
            "message": f"A 6-digit verification code has been sent to {normalized_email}. Please check your inbox.",
            "email": normalized_email
        }

@router.post("/reset-password")
async def reset_password(req: ResetPasswordRequest):
    """Verifies reset code and updates password, returning authenticated user session."""
    normalized_email = req.email.lower().strip()
    provided_code = req.reset_code.strip()
    
    if len(req.new_password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    
    record = _RESET_CODES.get(normalized_email)
    if not record:
        raise HTTPException(status_code=400, detail="No active password reset request found. Please request a new code.")
    
    if time.time() > record["expires_at"]:
        _RESET_CODES.pop(normalized_email, None)
        raise HTTPException(status_code=400, detail="Reset code has expired. Please request a new code.")
    
    # Increment failed attempts counter (Brute-force protection)
    record["attempts"] = record.get("attempts", 0) + 1
    if record["attempts"] > 5:
        _RESET_CODES.pop(normalized_email, None)
        raise HTTPException(
            status_code=400, 
            detail="Too many failed verification attempts. For your security, this code has been invalidated. Please request a new one."
        )

    if record["code"] != provided_code:
        remaining = max(0, 5 - record["attempts"])
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid verification code. Please check and try again. ({remaining} attempts remaining)"
        )
    
    # Code is valid - update password in database
    async with AsyncSessionLocal() as session:
        stmt = select(DBUser).where(DBUser.email == normalized_email)
        res = await session.execute(stmt)
        user = res.scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=404, detail="User account not found")
        
        user.hashed_password = hash_password(req.new_password)
        await session.commit()
        await session.refresh(user)
        
        # Invalidate used reset code immediately
        _RESET_CODES.pop(normalized_email, None)
        
        token = create_access_token({"sub": str(user.id), "email": user.email})
        
        logger.info(f"Password successfully reset for user {normalized_email}")
        
        return {
            "status": "success",
            "message": "Password reset successfully! You are now logged in.",
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
