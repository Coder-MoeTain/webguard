"""
WebGuard RF - Authentication API
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..core.security import verify_password, get_password_hash, create_access_token
from ..db import get_db, db_available
from ..db.models import User

router = APIRouter()

# Fallback for when DB is not available
DEMO_USERS = {"admin": ("admin123", "admin")}


class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str
    role: str = "researcher"


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str
    role: str


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest):
    if db_available():
        with get_db() as db:
            if db:
                user = db.query(User).filter(User.username == req.username).first()
                if user and user.is_active and verify_password(req.password, user.hashed_password):
                    token = create_access_token({"sub": user.username, "role": user.role})
                    return TokenResponse(access_token=token, username=user.username, role=user.role)
    if req.username in DEMO_USERS and DEMO_USERS[req.username][0] == req.password:
        token = create_access_token({"sub": req.username, "role": DEMO_USERS[req.username][1]})
        return TokenResponse(access_token=token, username=req.username, role=DEMO_USERS[req.username][1])
    raise HTTPException(status_code=401, detail="Invalid credentials")


@router.post("/register", response_model=TokenResponse)
def register(req: RegisterRequest):
    if db_available():
        with get_db() as db:
            if db:
                if db.query(User).filter(User.username == req.username).first():
                    raise HTTPException(status_code=400, detail="Username already exists")
                if db.query(User).filter(User.email == req.email).first():
                    raise HTTPException(status_code=400, detail="Email already exists")
                user = User(
                    username=req.username,
                    email=req.email,
                    hashed_password=get_password_hash(req.password),
                    role=req.role,
                )
                db.add(user)
                db.flush()
                token = create_access_token({"sub": user.username, "role": user.role})
                return TokenResponse(access_token=token, username=user.username, role=user.role)
    token = create_access_token({"sub": req.username, "role": req.role})
    return TokenResponse(access_token=token, username=req.username, role=req.role)
