"""
Quiz router — AI-powered grammar quiz generation and submission.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import QuizSession, User, ActivityLog
from app.schemas import (
    QuizGenerateRequest, QuizQuestion,
    QuizSubmitRequest, QuizSessionResponse
)
from app.dependencies import require_student
from app.services.groq_service import generate_quiz_questions
from app.limiter import limiter

router = APIRouter()


@router.post("/generate", response_model=list[QuizQuestion])
@limiter.limit("15/minute")
async def generate_quiz(
    request: Request,
    payload: QuizGenerateRequest,
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db)
):
    """Generate AI-powered MCQ grammar questions."""
    try:
        questions = await generate_quiz_questions(
            topic=payload.topic,
            difficulty=payload.difficulty,
            num_questions=payload.num_questions
        )
        return questions
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Quiz generation failed: {str(e)}")


@router.post("/submit", response_model=QuizSessionResponse, status_code=201)
def submit_quiz(
    request: QuizSubmitRequest,
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db)
):
    """Save quiz results, award points, and log activity."""
    try:
        quiz_session = QuizSession(
            student_id=current_user.id,
            score=request.score,
            total_questions=request.total_questions
        )
        db.add(quiz_session)

        # Award 5 points for quiz completion
        current_user.total_points += 5
        db.add(ActivityLog(
            user_id=current_user.id,
            action="quiz_completed",
            metadata_={
                "score": request.score,
                "total": request.total_questions,
                "points_earned": 5
            }
        ))

        db.commit()
        db.refresh(quiz_session)
        return quiz_session
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
