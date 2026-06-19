"""
Owner router — manage students, teachers, and view organization dashboard.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models import User, AllowedStudent, Organization, Assignment
from app.schemas import (
    AllowedStudentCreate, AllowedStudentResponse,
    OwnerDashboardResponse, OrganizationResponse, UserResponse, AssignmentResponse
)
from app.dependencies import require_owner

router = APIRouter()


@router.get("/dashboard", response_model=OwnerDashboardResponse)
def get_owner_dashboard(
    current_user: User = Depends(require_owner),
    db: Session = Depends(get_db)
):
    """Get organization overview including stats and student list."""
    try:
        org = db.query(Organization).filter(
            Organization.id == current_user.organization_id
        ).first()
        if not org:
            raise HTTPException(status_code=404, detail="Organization not found")

        total_students = db.query(User).filter(
            User.organization_id == current_user.organization_id,
            User.role == "student"
        ).count()

        total_teachers = db.query(User).filter(
            User.organization_id == current_user.organization_id,
            User.role == "teacher"
        ).count()

        students = db.query(AllowedStudent).filter(
            AllowedStudent.organization_id == current_user.organization_id,
            AllowedStudent.role == "student"
        ).all()

        teachers_whitelist = db.query(AllowedStudent).filter(
            AllowedStudent.organization_id == current_user.organization_id,
            AllowedStudent.role == "teacher"
        ).all()

        student_responses = []
        for s in students:
            user_exists = db.query(User).filter(
                User.organization_id == current_user.organization_id,
                User.email == s.email,
                User.role == "student"
            ).first() is not None
            
            student_responses.append(
                AllowedStudentResponse(
                    id=s.id,
                    organization_id=s.organization_id,
                    email=s.email,
                    role=s.role,
                    is_active=not user_exists,
                    added_by=s.added_by,
                    added_at=s.added_at
                )
            )

        teacher_responses = []
        for t in teachers_whitelist:
            user_exists = db.query(User).filter(
                User.organization_id == current_user.organization_id,
                User.email == t.email,
                User.role == "teacher"
            ).first() is not None
            
            teacher_responses.append(
                AllowedStudentResponse(
                    id=t.id,
                    organization_id=t.organization_id,
                    email=t.email,
                    role=t.role,
                    is_active=not user_exists,
                    added_by=t.added_by,
                    added_at=t.added_at
                )
            )

        return OwnerDashboardResponse(
            organization=OrganizationResponse.model_validate(org),
            total_students=total_students,
            total_teachers=total_teachers,
            students=student_responses,
            teachers=teacher_responses
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load dashboard: {str(e)}")


@router.get("/students", response_model=list[AllowedStudentResponse])
def get_allowed_students(
    current_user: User = Depends(require_owner),
    db: Session = Depends(get_db)
):
    """Get all whitelisted student emails for this organization."""
    try:
        students = db.query(AllowedStudent).filter(
            AllowedStudent.organization_id == current_user.organization_id,
            AllowedStudent.role == "student"
        ).all()

        student_responses = []
        for s in students:
            user_exists = db.query(User).filter(
                User.organization_id == current_user.organization_id,
                User.email == s.email,
                User.role == "student"
            ).first() is not None
            
            student_responses.append(
                AllowedStudentResponse(
                    id=s.id,
                    organization_id=s.organization_id,
                    email=s.email,
                    role=s.role,
                    is_active=not user_exists,
                    added_by=s.added_by,
                    added_at=s.added_at
                )
            )
        return student_responses
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/students", response_model=AllowedStudentResponse, status_code=201)
def add_student_email(
    request: AllowedStudentCreate,
    current_user: User = Depends(require_owner),
    db: Session = Depends(get_db)
):
    """
    Add a student email to the whitelist.
    Checks seat availability before adding.
    """
    try:
        org = db.query(Organization).filter(
            Organization.id == current_user.organization_id
        ).first()

        if not org:
            raise HTTPException(status_code=404, detail="Organization not found")

        # Check seat availability
        if org.seats_used >= org.max_seats:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Seat limit reached ({org.max_seats}). Upgrade your plan."
            )

        # Check for duplicate
        existing = db.query(AllowedStudent).filter(
            AllowedStudent.organization_id == current_user.organization_id,
            AllowedStudent.email == request.email
        ).first()

        if existing:
            raise HTTPException(status_code=400, detail="Email already whitelisted")

        new_student = AllowedStudent(
            organization_id=current_user.organization_id,
            email=request.email,
            role="student",
            added_by=current_user.id
        )
        db.add(new_student)
        org.seats_used += 1
        db.commit()
        db.refresh(new_student)

        return new_student
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/students/{email}")
def remove_student_email(
    email: str,
    current_user: User = Depends(require_owner),
    db: Session = Depends(get_db)
):
    """Hard delete a whitelisted email (and its registered user) from the database."""
    try:
        # Find whitelist entry (could be student or teacher role)
        allowed = db.query(AllowedStudent).filter(
            AllowedStudent.organization_id == current_user.organization_id,
            AllowedStudent.email == email
        ).first()

        # Find registered user entry if exists
        user = db.query(User).filter(
            User.organization_id == current_user.organization_id,
            User.email == email
        ).first()

        if not allowed and not user:
            raise HTTPException(status_code=404, detail="Email not found in organization whitelists or registered users")

        # Determine if it's a student to adjust seat usage
        is_student = False
        if allowed:
            if allowed.role == "student":
                is_student = True
            db.delete(allowed)

        if user:
            if user.role == "student":
                is_student = True
            db.delete(user)

        # Decrement seats if it was a student
        if is_student:
            org = db.query(Organization).filter(
                Organization.id == current_user.organization_id
            ).first()
            if org and org.seats_used > 0:
                org.seats_used -= 1

        db.commit()
        return {"message": f"Email {email} removed successfully"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/students/registered", response_model=list[UserResponse])
def get_registered_students(
    current_user: User = Depends(require_owner),
    db: Session = Depends(get_db)
):
    """Get all registered student users in this organization."""
    try:
        students = db.query(User).filter(
            User.organization_id == current_user.organization_id,
            User.role == "student"
        ).order_by(User.first_name).all()
        return students
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/teachers", response_model=list[UserResponse])
def get_teachers(
    current_user: User = Depends(require_owner),
    db: Session = Depends(get_db)
):
    """Get all teachers in this organization."""
    try:
        teachers = db.query(User).filter(
            User.organization_id == current_user.organization_id,
            User.role == "teacher"
        ).all()
        return teachers
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/teachers", response_model=AllowedStudentResponse, status_code=201)
def add_teacher_email(
    request: AllowedStudentCreate,
    current_user: User = Depends(require_owner),
    db: Session = Depends(get_db)
):
    """Add a teacher email to the organization whitelist."""
    try:
        existing = db.query(AllowedStudent).filter(
            AllowedStudent.organization_id == current_user.organization_id,
            AllowedStudent.email == request.email
        ).first()

        if existing:
            raise HTTPException(status_code=400, detail="Email already exists")

        new_teacher = AllowedStudent(
            organization_id=current_user.organization_id,
            email=request.email,
            role="teacher",
            added_by=current_user.id
        )
        db.add(new_teacher)
        db.commit()
        db.refresh(new_teacher)

        return new_teacher
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/assignments", response_model=list[AssignmentResponse])
def get_owner_assignments(
    current_user: User = Depends(require_owner),
    db: Session = Depends(get_db)
):
    """Get all assignments created under the owner's organization."""
    try:
        assignments = db.query(Assignment).filter(
            Assignment.organization_id == current_user.organization_id
        ).order_by(Assignment.created_at.desc()).all()
        return assignments
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
