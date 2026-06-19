"""
Progress router — scores over time and tenses mastery data.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, func

from app.database import get_db
from app.models import (
    User, VoiceSession, QuizSession,
    StudentTenseProgress, StudentVocabulary, Tense
)
from app.schemas import (
    ProgressOverview, StudentTenseProgressResponse,
    QuizSessionResponse, VoiceSessionResponse, TenseResponse
)
from app.dependencies import require_student

router = APIRouter()


@router.get("/", response_model=ProgressOverview)
def get_progress(
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db)
):
    """Get comprehensive progress data for the student."""
    try:
        # Voice sessions
        voice_sessions = db.query(VoiceSession).filter(
            VoiceSession.student_id == current_user.id
        ).order_by(desc(VoiceSession.created_at)).limit(10).all()

        # Quiz sessions
        quiz_sessions = db.query(QuizSession).filter(
            QuizSession.student_id == current_user.id
        ).order_by(desc(QuizSession.created_at)).limit(10).all()

        # Average score
        avg_result = db.query(
            func.avg(VoiceSession.overall_score)
        ).filter(
            VoiceSession.student_id == current_user.id,
            VoiceSession.overall_score.isnot(None)
        ).scalar()
        avg_score = float(avg_result) if avg_result else 0.0

        # Tense mastery
        tense_progress = db.query(StudentTenseProgress).options(
            joinedload(StudentTenseProgress.tense)
        ).filter(
            StudentTenseProgress.student_id == current_user.id
        ).all()

        # Words learned count (last 24 hours)
        from datetime import datetime, timedelta
        cutoff = datetime.utcnow() - timedelta(hours=24)

        words_learned = db.query(StudentVocabulary).filter(
            StudentVocabulary.student_id == current_user.id,
            StudentVocabulary.learned == True,
            StudentVocabulary.learned_at >= cutoff
        ).count()

        daily_voice_count = db.query(VoiceSession).filter(
            VoiceSession.student_id == current_user.id,
            VoiceSession.created_at >= cutoff
        ).count()
        daily_quiz_count = db.query(QuizSession).filter(
            QuizSession.student_id == current_user.id,
            QuizSession.created_at >= cutoff
        ).count()
        total_sessions = daily_voice_count + daily_quiz_count

        # Sync streak
        from app.services.streak_helper import sync_user_streak
        sync_user_streak(current_user, db)

        return ProgressOverview(
            total_sessions=total_sessions,
            avg_score=round(avg_score, 1),
            words_learned=words_learned,
            current_streak=current_user.current_streak,
            total_points=current_user.total_points,
            tense_mastery=[
                StudentTenseProgressResponse.model_validate(tp)
                for tp in tense_progress
            ],
            recent_quiz_scores=[
                QuizSessionResponse.model_validate(qs)
                for qs in quiz_sessions
            ],
            recent_voice_sessions=[
                VoiceSessionResponse.model_validate(vs)
                for vs in voice_sessions
            ],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
