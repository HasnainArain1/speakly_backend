from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
import logging
from datetime import datetime

from app.database import get_db
from app.models import User, GrammarLesson, StudentGrammarProgress, ActivityLog
from app.schemas import (
    GrammarLessonResponse, GrammarProgressResponse,
    ExerciseSubmit, ExercisesResponse
)
from app.dependencies import require_student
from app.limiter import limiter
from app.services.groq_service import generate_grammar_lesson_exercises, generate_grammar_lesson_content

router = APIRouter()
logger = logging.getLogger("speakly")


@router.get("/", response_model=List[GrammarLessonResponse])
def get_grammar_lessons(
    category: Optional[str] = None,
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db)
):
    """Fetch grammar lessons, optionally filtered by category, ordered by order_index."""
    try:
        query = db.query(GrammarLesson)
        if category:
            query = query.filter(GrammarLesson.category == category)
        lessons = query.order_by(GrammarLesson.order_index).all()
        return lessons
    except Exception as e:
        logger.error(f"Failed to fetch grammar lessons: {str(e)}")
        raise HTTPException(status_code=500, detail="Server error")


@router.get("/categories", response_model=List[str])
def get_categories(
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db)
):
    """Return distinct categories list."""
    try:
        categories = ["voice", "speech", "articles", "conditionals", "comparison", "prepositions"]
        return categories
    except Exception as e:
        logger.error(f"Failed to fetch categories: {str(e)}")
        raise HTTPException(status_code=500, detail="Server error")


@router.get("/progress")
def get_grammar_progress(
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db)
):
    """Fetch all grammar lessons progress grouped by category."""
    try:
        results = db.query(GrammarLesson, StudentGrammarProgress).outerjoin(
            StudentGrammarProgress,
            (StudentGrammarProgress.lesson_id == GrammarLesson.id) & 
            (StudentGrammarProgress.student_id == current_user.id)
        ).order_by(GrammarLesson.order_index).all()

        categories = ["voice", "speech", "articles", "conditionals", "comparison", "prepositions"]
        grouped_progress = {cat: [] for cat in categories}

        for lesson, progress in results:
            attempts = progress.attempts if progress else 0
            correct_count = progress.correct_count if progress else 0
            is_completed = progress.is_completed if progress else False
            
            mastery_percent = 0
            if attempts > 0:
                mastery_percent = round((correct_count / attempts) * 100)
                
            lesson_progress = {
                "id": lesson.id,
                "name": lesson.name,
                "mastery_percent": mastery_percent,
                "is_completed": is_completed,
                "last_practiced_at": progress.last_practiced_at if progress else None
            }
            
            cat = lesson.category.lower() if lesson.category else ""
            if cat in grouped_progress:
                grouped_progress[cat].append(lesson_progress)
            else:
                # fallback for unknown categories
                if cat not in grouped_progress:
                    grouped_progress[cat] = []
                grouped_progress[cat].append(lesson_progress)

        return grouped_progress
    except Exception as e:
        logger.error(f"Failed to fetch grammar lessons progress: {str(e)}")
        raise HTTPException(status_code=500, detail="Server error")


@router.get("/{id}", response_model=GrammarLessonResponse)
def get_grammar_lesson(
    id: int,
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db)
):
    """Fetch single grammar lesson by id."""
    try:
        lesson = db.query(GrammarLesson).filter(GrammarLesson.id == id).first()
        if not lesson:
            raise HTTPException(status_code=404, detail="Grammar lesson not found")
        return lesson
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch grammar lesson: {str(e)}")
        raise HTTPException(status_code=500, detail="Server error")


@router.post("/{id}/generate-exercise")
@limiter.limit("15/minute")
def generate_exercise(
    request: Request,
    id: int,
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db)
):
    """Call Groq LLaMA 3 8B to generate 5 exercises for grammar lesson."""
    try:
        lesson = db.query(GrammarLesson).filter(GrammarLesson.id == id).first()
        if not lesson:
            raise HTTPException(status_code=404, detail="Grammar lesson not found")

        # Call service to generate exercises
        content = generate_grammar_lesson_content(lesson.name, lesson.rules)
        return content
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate exercises for grammar lesson {id}: {str(e)}")
        raise HTTPException(status_code=503, detail="AI service unavailable")


@router.post("/{id}/generate-content")
@limiter.limit("10/minute")
def generate_lesson_content(
    request: Request,
    id: int,
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db)
):
    """Generate full lesson content: explanation, examples, and exercises."""
    try:
        lesson = db.query(GrammarLesson).filter(GrammarLesson.id == id).first()
        if not lesson:
            raise HTTPException(status_code=404, detail="Grammar lesson not found")

        content = generate_grammar_lesson_content(lesson.name, lesson.rules)
        return content
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate lesson content for grammar lesson {id}: {str(e)}")
        raise HTTPException(status_code=503, detail="AI service unavailable")


@router.post("/{id}/submit")
def submit_exercise(
    id: int,
    payload: ExerciseSubmit,
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db)
):
    """Submit grammar lesson practice results, update stats and user points."""
    try:
        lesson = db.query(GrammarLesson).filter(GrammarLesson.id == id).first()
        if not lesson:
            raise HTTPException(status_code=404, detail="Grammar lesson not found")

        progress = db.query(StudentGrammarProgress).filter(
            StudentGrammarProgress.student_id == current_user.id,
            StudentGrammarProgress.lesson_id == id
        ).first()

        if not progress:
            progress = StudentGrammarProgress(
                student_id=current_user.id,
                lesson_id=id,
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
            action="grammar_lesson_practice",
            metadata_={
                "lesson_id": id,
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
        logger.error(f"Failed to submit grammar lesson exercise progress: {str(e)}")
        raise HTTPException(status_code=500, detail="Server error")
