"""
FastAPI dependencies for JWT authentication and role-based access control.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas import UserResponse
from app.services.auth_service import decode_access_token

security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Validate JWT token and return the current user.
    
    Raises:
        HTTPException 401: If token is missing, invalid, or expired.
        HTTPException 401: If user not found in database.
    """
    token = credentials.credentials
    payload = decode_access_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    
    return user


def require_student(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Require the current user to have 'student' role.
    
    Raises:
        HTTPException 403: If user is not a student.
    """
    if current_user.role != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Student role required.",
        )
    return current_user


def require_teacher(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Require the current user to have 'teacher' role.
    
    Raises:
        HTTPException 403: If user is not a teacher.
    """
    if current_user.role != "teacher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Teacher role required.",
        )
    return current_user


def require_owner(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Require the current user to have 'owner' role.
    
    Raises:
        HTTPException 403: If user is not an owner.
    """
    if current_user.role != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Owner role required.",
        )
    return current_user


def require_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Require the current user to have 'super_admin' role.
    
    Raises:
        HTTPException 403: If user is not a super admin.
    """
    if current_user.role != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Super admin role required.",
        )
    return current_user
