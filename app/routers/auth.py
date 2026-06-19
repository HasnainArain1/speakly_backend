"""
Authentication router — register, login, and current user endpoints.
Implements the exact login flow specified in the requirements.
"""

import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.limiter import limiter

from app.database import get_db
from app.models import User, AllowedStudent, Organization, ActivityLog
from app.schemas import (
    LoginRequest, LoginResponse, UserResponse,
    UserCreate
)
from app.services.auth_service import (
    verify_password, create_access_token, hash_password
)
from app.dependencies import get_current_user

logger = logging.getLogger("speakly.auth")
router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=201)
def register(request: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user account.

    Flow:
    1. Check if email already exists → 409 Conflict
    2. For students: verify email is whitelisted → 403
    3. For students: verify organization has available seats → 400
    4. Hash password, create user
    5. Increment organization seats_used
    """
    try:
        # Step 1: Check duplicate email
        existing = db.query(User).filter(User.email == request.email).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this email already exists"
            )

        # Step 2: Whitelist check for role
        if request.role in ("student", "teacher"):
            allowed = db.query(AllowedStudent).filter(
                AllowedStudent.email == request.email,
                AllowedStudent.role == request.role,
                AllowedStudent.is_active == True
            ).first()
            if not allowed:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Your email is not whitelisted for a {request.role} account. Contact your coaching center."
                )
            # Auto-assign organization from whitelist
            request.organization_id = allowed.organization_id

        # Step 3: Verify seat availability
        org = None
        if request.organization_id:
            org = db.query(Organization).filter(
                Organization.id == request.organization_id
            ).first()
            if org and request.role == "student":
                if org.seats_used >= org.max_seats:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Seat limit reached ({org.max_seats}). Contact your coaching center."
                    )

        # Step 4: Create user
        user = User(
            email=request.email,
            password_hash=hash_password(request.password),
            first_name=request.first_name,
            last_name=request.last_name,
            role=request.role,
            organization_id=request.organization_id,
        )
        db.add(user)

        db.commit()
        db.refresh(user)

        logger.info(f"User registered: {user.email} (role={user.role})")
        return user

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Registration failed for {request.email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )


@router.post("/login", response_model=LoginResponse)
@limiter.limit("5/minute")
def login(request: Request, payload: LoginRequest, db: Session = Depends(get_db)):
    """
    Authenticate user with email and password.

    Flow:
    1. Find user by email → 401 if not found
    2. Check allowed_students whitelist (for students) → 403 if not whitelisted
    3. Check organization is active → 403 if subscription expired
    4. Verify bcrypt password → 401 if wrong
    5. Generate JWT → return token
    """
    try:
        # Step 1: Find user by email
        user = db.query(User).filter(User.email == payload.email).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account not found"
            )

        # Step 2: Check whitelist (for student and teacher roles)
        if user.role in ("student", "teacher"):
            allowed = db.query(AllowedStudent).filter(
                AllowedStudent.email == payload.email,
                AllowedStudent.role == user.role,
                AllowedStudent.is_active == True
            ).first()
            if not allowed:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied. Your email is not whitelisted or role mismatch."
                )

        # Step 3: Check organization is active
        if user.organization_id:
            org = db.query(Organization).filter(
                Organization.id == user.organization_id
            ).first()
            if org and not org.is_active:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Subscription expired. Contact Speakly support."
                )

        # Step 4: Verify password
        if not verify_password(payload.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect password"
            )

        # Step 5: Generate JWT
        token_data = {
            "sub": str(user.id),
            "role": user.role,
            "org_id": str(user.organization_id) if user.organization_id else None,
            "name": user.first_name,
        }
        access_token = create_access_token(data=token_data)

        # Update last login
        user.last_login = datetime.utcnow()

        # Log daily login activity & award points
        db.add(ActivityLog(
            user_id=user.id,
            action="daily_login",
            metadata_={"points_earned": 2}
        ))
        user.total_points += 2

        db.commit()

        # Sync streak
        from app.services.streak_helper import sync_user_streak
        sync_user_streak(user, db)

        logger.info(f"User logged in: {user.email} (role={user.role})")
        return LoginResponse(
            access_token=access_token,
            role=user.role,
            name=user.first_name
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login failed for {payload.email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Get the current authenticated user's profile data."""
    return current_user


# ==================== DEMO SIGNUP (TEMPORARY — FOR MVP TESTING) ====================

import os

DEMO_MODE_ENABLED = os.getenv("DEMO_MODE_ENABLED", "false").lower() == "true"
DEMO_ORG_ID = os.getenv("DEMO_ORG_ID", None)


@router.get("/config")
def get_config():
    """
    Public config endpoint — tells frontend if demo signup is available.
    TEMPORARY: Remove when real coaching centers are onboarded.
    """
    return {"demo_mode_enabled": DEMO_MODE_ENABLED}


@router.post("/demo-signup", response_model=LoginResponse)
@limiter.limit("3/hour")
def demo_signup(request: Request, payload: UserCreate, db: Session = Depends(get_db)):
    """
    TEMPORARY demo signup endpoint for MVP testing.

    Allows anyone to create a student account in the "Speakly Demo"
    organization without needing an owner to whitelist them first.

    Controlled by DEMO_MODE_ENABLED env var — set to false to disable.
    """
    try:
        # Step 1: Check if demo mode is enabled
        if not DEMO_MODE_ENABLED or not DEMO_ORG_ID:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Demo signup is currently disabled"
            )

        # Step 2: Check if email already exists
        existing = db.query(User).filter(User.email == payload.email).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Account already exists, please login instead"
            )

        # Step 3: Check seat availability in demo org
        org = db.query(Organization).filter(
            Organization.id == DEMO_ORG_ID
        ).first()
        if not org:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Demo organization not configured properly"
            )
        if org.seats_used >= org.max_seats:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Demo is full, please try again later"
            )

        # Step 4: Hash the password
        hashed = hash_password(payload.password)

        # Step 5: Auto-whitelist this email in allowed_students
        whitelist_entry = AllowedStudent(
            organization_id=DEMO_ORG_ID,
            email=payload.email,
            role="student",
            is_active=True,
            added_by=None
        )
        db.add(whitelist_entry)

        # Step 6: Create the user account
        user = User(
            organization_id=DEMO_ORG_ID,
            email=payload.email,
            password_hash=hashed,
            first_name=payload.first_name,
            last_name=payload.last_name,
            role="student",
            is_active=True,
        )
        db.add(user)

        # Step 7: Increment seats_used
        org.seats_used += 1

        db.commit()
        db.refresh(user)

        # Step 8: Generate JWT token (same as normal login)
        token_data = {
            "sub": str(user.id),
            "role": user.role,
            "org_id": str(user.organization_id),
            "name": user.first_name,
        }
        access_token = create_access_token(data=token_data)

        # Log activity
        db.add(ActivityLog(
            user_id=user.id,
            action="demo_signup",
            metadata_={"source": "demo_signup"}
        ))
        db.commit()

        # Sync streak
        from app.services.streak_helper import sync_user_streak
        sync_user_streak(user, db)

        logger.info(f"Demo signup: {user.email}")
        return LoginResponse(
            access_token=access_token,
            role=user.role,
            name=user.first_name
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Demo signup failed for {payload.email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Demo signup failed: {str(e)}"
        )
