"""
Tenses router — list tenses, generate AI exercises, and save progress.
"""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Tense, StudentTenseProgress, User, ActivityLog
from app.schemas import TenseResponse, TenseExercise, TenseSubmitRequest
from app.dependencies import require_student, get_current_user
from app.services.groq_service import generate_tense_exercises
from app.limiter import limiter

router = APIRouter()


@router.get("/", response_model=list[TenseResponse])
def get_all_tenses(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all 12 English tenses with formulas and explanations, plus student progress."""
    try:
        tenses = db.query(Tense).order_by(Tense.id).all()
        progress_records = {
            p.tense_id: p 
            for p in db.query(StudentTenseProgress).filter(StudentTenseProgress.student_id == current_user.id).all()
        }
        
        response = []
        for t in tenses:
            p = progress_records.get(t.id)
            response.append(TenseResponse(
                id=t.id,
                name=t.name,
                formula=t.formula,
                explanation=t.explanation,
                urdu_explanation=t.urdu_explanation,
                example=t.example,
                mastery_percent=p.mastery_percent if p else 0,
                last_practiced_at=p.last_practiced_at if p else None
            ))
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{tense_id}", response_model=TenseResponse)
def get_tense(
    tense_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a single tense by ID with full details."""
    try:
        tense = db.query(Tense).filter(Tense.id == tense_id).first()
        if not tense:
            raise HTTPException(status_code=404, detail="Tense not found")
        return tense
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{tense_id}/generate-exercise", response_model=list[TenseExercise])
@limiter.limit("15/minute")
async def generate_exercise(
    request: Request,
    tense_id: int,
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db)
):
    """Generate 5 AI-powered fill-in-the-blank exercises for a tense."""
    try:
        tense = db.query(Tense).filter(Tense.id == tense_id).first()
        if not tense:
            raise HTTPException(status_code=404, detail="Tense not found")

        exercises = await generate_tense_exercises(tense.name)
        return exercises
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{tense_id}/submit")
def submit_tense_progress(
    tense_id: int,
    request: TenseSubmitRequest,
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db)
):
    """Save student's tense practice progress and award points."""
    try:
        tense = db.query(Tense).filter(Tense.id == tense_id).first()
        if not tense:
            raise HTTPException(status_code=404, detail="Tense not found")

        # Upsert progress
        progress = db.query(StudentTenseProgress).filter(
            StudentTenseProgress.student_id == current_user.id,
            StudentTenseProgress.tense_id == tense_id
        ).first()

        if progress:
            # Only update if new score is higher
            if request.mastery_percent > progress.mastery_percent:
                progress.mastery_percent = request.mastery_percent
            progress.last_practiced_at = datetime.utcnow()
        else:
            progress = StudentTenseProgress(
                student_id=current_user.id,
                tense_id=tense_id,
                mastery_percent=request.mastery_percent,
                last_practiced_at=datetime.utcnow()
            )
            db.add(progress)

        # Award points for tense practice
        current_user.total_points += 3
        db.add(ActivityLog(
            user_id=current_user.id,
            action="tense_practice",
            metadata_={"tense_id": tense_id, "mastery": request.mastery_percent, "points_earned": 3}
        ))

        db.commit()
        return {"message": "Progress saved", "mastery_percent": request.mastery_percent, "points_earned": 3}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
