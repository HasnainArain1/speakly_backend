"""
Teacher router — dashboard, student progress, assignments.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
import uuid

from app.database import get_db
from app.models import (
    User, Assignment, AssignmentSubmission,
    VoiceSession, QuizSession, ActivityLog
)
from app.schemas import (
    TeacherDashboardResponse, AssignmentCreate,
    AssignmentResponse, UserResponse, AssignmentSubmissionDetail
)
from app.dependencies import require_teacher

from app.services.groq_service import generate_ai_assignment

router = APIRouter()


@router.get("/dashboard", response_model=TeacherDashboardResponse)
def get_teacher_dashboard(
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db)
):
    """Get teacher dashboard stats."""
    try:
        org_id = current_user.organization_id
        total_students = db.query(User).filter(
            User.organization_id == org_id,
            User.role == "student"
        ).count()

        total_assignments = db.query(Assignment).filter(
            Assignment.teacher_id == current_user.id
        ).count()

        avg = db.query(func.avg(VoiceSession.overall_score)).join(
            User, VoiceSession.student_id == User.id
        ).filter(
            User.organization_id == org_id,
            VoiceSession.overall_score.isnot(None)
        ).scalar()

        return TeacherDashboardResponse(
            total_students=total_students,
            total_assignments=total_assignments,
            avg_score=round(float(avg), 1) if avg else 0.0,
            recent_activity=[]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/students", response_model=list[UserResponse])
def get_students(
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db)
):
    """Get all students in the teacher's organization."""
    try:
        students = db.query(User).filter(
            User.organization_id == current_user.organization_id,
            User.role == "student"
        ).order_by(User.first_name).all()
        return students
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/assignments", response_model=AssignmentResponse, status_code=201)
async def create_assignment(
    request: AssignmentCreate,
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db)
):
    """Create a new assignment for the organization (can generate with AI)."""
    try:
        title = request.title
        description = request.description

        if request.topic:
            ai_data = await generate_ai_assignment(request.topic)
            title = ai_data.get("title", f"Assignment: Practice {request.topic}")
            description = ai_data.get("description", f"AI Generated exercises for {request.topic}")

        if not title:
            raise HTTPException(status_code=400, detail="Title or topic is required")

        assignment = Assignment(
            organization_id=current_user.organization_id,
            teacher_id=current_user.id,
            title=title,
            description=description,
            max_score=request.max_score,
            due_date=request.due_date
        )
        db.add(assignment)
        db.commit()
        db.refresh(assignment)
        return assignment
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/assignments/generate-preview")
async def generate_preview(
    request: AssignmentCreate,
    current_user: User = Depends(require_teacher)
):
    """Generate assignment title and content preview with AI without saving it yet."""
    if not request.topic:
        raise HTTPException(status_code=400, detail="Topic is required")
    try:
        ai_data = await generate_ai_assignment(request.topic)
        return ai_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate preview: {str(e)}")


@router.get("/assignments", response_model=list[AssignmentResponse])
def get_assignments(
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db)
):
    """Get all assignments created by this teacher."""
    try:
        assignments = db.query(Assignment).filter(
            Assignment.teacher_id == current_user.id
        ).order_by(desc(Assignment.created_at)).all()
        return assignments
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/students/{student_id}/progress")
def get_student_progress(
    student_id: uuid.UUID,
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db)
):
    """Get detailed progress for a specific student."""
    try:
        student = db.query(User).filter(
            User.id == student_id,
            User.organization_id == current_user.organization_id,
            User.role == "student"
        ).first()
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")

        voice = db.query(VoiceSession).filter(
            VoiceSession.student_id == student_id
        ).order_by(desc(VoiceSession.created_at)).limit(5).all()

        quizzes = db.query(QuizSession).filter(
            QuizSession.student_id == student_id
        ).order_by(desc(QuizSession.created_at)).limit(5).all()

        return {
            "student": UserResponse.model_validate(student),
            "voice_sessions": [
                {"id": str(v.id), "score": v.overall_score, "date": str(v.created_at)}
                for v in voice
            ],
            "quiz_sessions": [
                {"id": str(q.id), "score": q.score, "total": q.total_questions, "date": str(q.created_at)}
                for q in quizzes
            ],
            "total_points": student.total_points,
            "current_streak": student.current_streak,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/assignments/submissions", response_model=list[AssignmentSubmissionDetail])
def get_teacher_assignment_submissions(
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db)
):
    """Get all student submissions for assignments created by this teacher."""
    try:
        submissions = db.query(
            AssignmentSubmission
        ).join(
            Assignment, AssignmentSubmission.assignment_id == Assignment.id
        ).filter(
            Assignment.teacher_id == current_user.id
        ).order_by(desc(AssignmentSubmission.submitted_at)).all()

        results = []
        for sub in submissions:
            student = sub.student
            assignment = sub.assignment
            results.append(
                AssignmentSubmissionDetail(
                    id=sub.id,
                    assignment_id=sub.assignment_id,
                    assignment_title=assignment.title if assignment else "Unknown Assignment",
                    student_id=sub.student_id,
                    student_name=f"{student.first_name} {student.last_name or ''}".strip() if student else "Unknown Student",
                    student_email=student.email if student else "Unknown Email",
                    score=sub.score,
                    feedback=sub.feedback,
                    submitted_at=sub.submitted_at
                )
            )
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
