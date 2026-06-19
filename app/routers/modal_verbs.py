from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List
import logging
from datetime import datetime

from app.database import get_db
from app.models import User, ModalVerb, StudentModalProgress, ActivityLog
from app.schemas import (
    ModalVerbResponse, ModalProgressResponse,
    ExerciseSubmit, ExercisesResponse
)
from app.dependencies import require_student
from app.limiter import limiter
from app.services.groq_service import generate_modal_verb_exercises

router = APIRouter()
logger = logging.getLogger("speakly")


@router.get("/", response_model=List[ModalVerbResponse])
def get_modal_verbs(
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db)
):
    """Fetch all 9 rows from modal_verbs table ordered by order_index."""
    try:
        verbs = db.query(ModalVerb).order_by(ModalVerb.order_index).all()
        return verbs
    except Exception as e:
        logger.error(f"Failed to fetch modal verbs: {str(e)}")
        raise HTTPException(status_code=500, detail="Server error")


@router.get("/progress", response_model=List[ModalProgressResponse])
def get_modal_progress(
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db)
):
    """Fetch all 9 modal verbs along with progress metrics for current student."""
    try:
        # Join modal_verbs with student_modal_progress
        results = db.query(ModalVerb, StudentModalProgress).outerjoin(
            StudentModalProgress,
            (StudentModalProgress.modal_verb_id == ModalVerb.id) & 
            (StudentModalProgress.student_id == current_user.id)
        ).order_by(ModalVerb.order_index).all()

        response_list = []
        for verb, progress in results:
            attempts = progress.attempts if progress else 0
            correct_count = progress.correct_count if progress else 0
            is_completed = progress.is_completed if progress else False
            
            mastery_percent = 0
            if attempts > 0:
                mastery_percent = round((correct_count / attempts) * 100)
                
            response_list.append(ModalProgressResponse(
                id=verb.id,
                name=verb.name,
                attempts=attempts,
                correct_count=correct_count,
                is_completed=is_completed,
                mastery_percent=mastery_percent,
                last_practiced_at=progress.last_practiced_at if progress else None
            ))
        return response_list
    except Exception as e:
        logger.error(f"Failed to fetch modal verbs progress: {str(e)}")
        raise HTTPException(status_code=500, detail="Server error")


@router.get("/{id}", response_model=ModalVerbResponse)
def get_modal_verb(
    id: int,
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db)
):
    """Fetch single modal verb by id."""
    try:
        verb = db.query(ModalVerb).filter(ModalVerb.id == id).first()
        if not verb:
            raise HTTPException(status_code=404, detail="Modal verb not found")
        return verb
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch modal verb: {str(e)}")
        raise HTTPException(status_code=500, detail="Server error")


@router.post("/{id}/generate-exercise")
@limiter.limit("15/minute")
def generate_exercise(
    request: Request,
    id: int,
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db)
):
    """Call Groq LLaMA 3 8B to generate 5 fill-in-the-blank exercises."""
    try:
        verb = db.query(ModalVerb).filter(ModalVerb.id == id).first()
        if not verb:
            raise HTTPException(status_code=404, detail="Modal verb not found")
        
        # Call service to generate exercises
        exercises = generate_modal_verb_exercises(verb.name, verb.usage)
        return {"exercises": exercises}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate exercises for modal verb {id}: {str(e)}")
        raise HTTPException(status_code=503, detail="AI service unavailable")


@router.post("/{id}/submit")
def submit_exercise(
    id: int,
    payload: ExerciseSubmit,
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db)
):
    """Submit modal practice results, update stats and user points."""
    try:
        verb = db.query(ModalVerb).filter(ModalVerb.id == id).first()
        if not verb:
            raise HTTPException(status_code=404, detail="Modal verb not found")

        progress = db.query(StudentModalProgress).filter(
            StudentModalProgress.student_id == current_user.id,
            StudentModalProgress.modal_verb_id == id
        ).first()

        if not progress:
            progress = StudentModalProgress(
                student_id=current_user.id,
                modal_verb_id=id,
                attempts=payload.total,
                correct_count=payload.correct_count,
                last_practiced_at=datetime.utcnow()
            )
            db.add(progress)
        else:
            progress.attempts += payload.total
            progress.correct_count += payload.correct_count
            progress.last_practiced_at = datetime.utcnow()

        # Recalculate mastery
        mastery_percent = 0
        if progress.attempts > 0:
            mastery_percent = round((progress.correct_count / progress.attempts) * 100)

        # Check completion threshold
        if mastery_percent >= 70:
            progress.is_completed = True

        # Award points
        current_user.total_points += 3

        # Add to logs
        db.add(ActivityLog(
            user_id=current_user.id,
            action="modal_verb_practice",
            metadata_={
                "modal_verb_id": id,
                "score": f"{payload.correct_count}/{payload.total}",
                "points_earned": 3
            }
        ))

        db.commit()
        db.refresh(progress)

        return {
            "mastery_percent": mastery_percent,
            "is_completed": progress.is_completed,
            "points_earned": 3
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to submit modal verb exercise progress: {str(e)}")
        raise HTTPException(status_code=500, detail="Server error")
