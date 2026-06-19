"""
Admin router — platform overview for super admins.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
import uuid

from app.database import get_db
from app.models import User, Organization
from app.schemas import (
    AdminDashboardResponse, OrganizationResponse,
    OrganizationUpdate, UserResponse
)
from app.dependencies import require_admin

router = APIRouter()


@router.get("/dashboard", response_model=AdminDashboardResponse)
def get_admin_dashboard(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get platform-wide stats for super admin."""
    try:
        total_orgs = db.query(Organization).count()
        active_orgs = db.query(Organization).filter(
            Organization.is_active == True
        ).count()
        total_users = db.query(User).count()
        total_students = db.query(User).filter(
            User.role == "student"
        ).count()

        orgs = db.query(Organization).order_by(
            Organization.created_at.desc()
        ).limit(20).all()

        return AdminDashboardResponse(
            total_organizations=total_orgs,
            total_users=total_users,
            total_students=total_students,
            active_organizations=active_orgs,
            organizations=[
                OrganizationResponse.model_validate(o) for o in orgs
            ]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/organizations", response_model=list[OrganizationResponse])
def get_organizations(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get all coaching centers."""
    try:
        orgs = db.query(Organization).order_by(
            Organization.created_at.desc()
        ).all()
        return orgs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/organizations/{org_id}", response_model=OrganizationResponse)
def update_organization(
    org_id: uuid.UUID,
    request: OrganizationUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Update organization plan or status."""
    try:
        org = db.query(Organization).filter(Organization.id == org_id).first()
        if not org:
            raise HTTPException(status_code=404, detail="Organization not found")

        if request.name is not None:
            org.name = request.name
        if request.plan is not None:
            org.plan = request.plan
        if request.max_seats is not None:
            org.max_seats = request.max_seats
        if request.is_active is not None:
            org.is_active = request.is_active

        db.commit()
        db.refresh(org)
        return org
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users", response_model=list[UserResponse])
def get_all_users(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get all users in the platform."""
    try:
        users = db.query(User).order_by(
            User.created_at.desc()
        ).limit(100).all()
        return users
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/organizations/{org_id}", status_code=204)
def delete_organization(
    org_id: uuid.UUID,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Delete an organization and all its associated data."""
    try:
        org = db.query(Organization).filter(Organization.id == org_id).first()
        if not org:
            raise HTTPException(status_code=404, detail="Organization not found")
        db.delete(org)
        db.commit()
        return None
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
