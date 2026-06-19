"""
Students router — home data, leaderboard.
"""

from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc

from app.database import get_db
from app.models import (
    User, Assignment, AssignmentSubmission, VoiceSession, QuizSession,
    WordOfDay, StudentVocabulary, ActivityLog
)
from app.schemas import (
    StudentHomeResponse, UserResponse, AssignmentResponse,
    WordOfDayResponse, LeaderboardEntry, AssignmentSubmissionCreate,
    AssignmentSubmissionResponse
)
from app.dependencies import require_student

router = APIRouter()


@router.get("/home", response_model=StudentHomeResponse)
def get_student_home(
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db)
):
    """Get student home page: stats, word of day, assignments, submissions."""
    try:
        # Word of day
        wod = db.query(WordOfDay).options(
            joinedload(WordOfDay.vocabulary)
        ).filter(
            WordOfDay.display_date == date.today()
        ).first()
        if not wod:
            wod = db.query(WordOfDay).options(
                joinedload(WordOfDay.vocabulary)
            ).order_by(WordOfDay.display_date.desc()).first()

        # Pending assignments
        assignments = []
        submissions = []
        if current_user.organization_id:
            assignments = db.query(Assignment).filter(
                Assignment.organization_id == current_user.organization_id
            ).order_by(Assignment.due_date.asc()).limit(5).all()

            assignment_ids = [a.id for a in assignments]
            if assignment_ids:
                submissions = db.query(AssignmentSubmission).filter(
                    AssignmentSubmission.student_id == current_user.id,
                    AssignmentSubmission.assignment_id.in_(assignment_ids)
                ).all()

        # Stats (last 24 hours only, to reset to zero after 24 hours)
        from datetime import timedelta
        cutoff = datetime.utcnow() - timedelta(hours=24)

        total_voice = db.query(VoiceSession).filter(
            VoiceSession.student_id == current_user.id,
            VoiceSession.created_at >= cutoff
        ).count()
        total_quiz = db.query(QuizSession).filter(
            QuizSession.student_id == current_user.id,
            QuizSession.created_at >= cutoff
        ).count()
        words_learned = db.query(StudentVocabulary).filter(
            StudentVocabulary.student_id == current_user.id,
            StudentVocabulary.learned == True,
            StudentVocabulary.learned_at >= cutoff
        ).count()

        # Sync streak
        from app.services.streak_helper import sync_user_streak
        sync_user_streak(current_user, db)

        stats = {
            "total_sessions": total_voice + total_quiz,
            "voice_sessions": total_voice,
            "quiz_sessions": total_quiz,
            "words_learned": words_learned,
            "total_points": current_user.total_points,
            "current_streak": current_user.current_streak,
        }

        return StudentHomeResponse(
            user=UserResponse.model_validate(current_user),
            word_of_day=wod,
            assignments=[AssignmentResponse.model_validate(a) for a in assignments],
            submissions=[AssignmentSubmissionResponse.model_validate(sub) for sub in submissions],
            stats=stats
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/leaderboard", response_model=list[LeaderboardEntry])
def get_leaderboard(
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db)
):
    """Get top 10 students in the same organization by daily points earned today."""
    try:
        from datetime import time
        from sqlalchemy import func

        # Get active date (UTC today)
        today_date = datetime.utcnow().date()

        query = db.query(User).filter(
            User.role == "student",
            User.is_active == True
        )
        if current_user.organization_id:
            query = query.filter(
                User.organization_id == current_user.organization_id
            )

        students = query.all()

        # Calculate daily points for each student
        student_daily_points = []
        for s in students:
            # Sync user's streak
            from app.services.streak_helper import sync_user_streak
            sync_user_streak(s, db)

            # Fetch all logs for today
            s_logs = db.query(ActivityLog).filter(
                ActivityLog.user_id == s.id,
                func.date(ActivityLog.created_at) == today_date
            ).all()

            daily_pts = 0
            for log in s_logs:
                if log.metadata_ and "points_earned" in log.metadata_:
                    try:
                        daily_pts += int(log.metadata_["points_earned"])
                    except (ValueError, TypeError):
                        continue

            student_daily_points.append({
                "student": s,
                "daily_points": daily_pts
            })

        # Sort by daily_points descending
        student_daily_points.sort(key=lambda x: x["daily_points"], reverse=True)
        top_entries = student_daily_points[:10]

        return [
            LeaderboardEntry(
                rank=idx + 1,
                id=entry["student"].id,
                first_name=entry["student"].first_name,
                last_name=entry["student"].last_name,
                total_points=entry["daily_points"],
                current_streak=entry["student"].current_streak
            )
            for idx, entry in enumerate(top_entries)
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/assignments/submit", response_model=AssignmentSubmissionResponse, status_code=201)
def submit_assignment(
    request: AssignmentSubmissionCreate,
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db)
):
    """Submit progress or answers for an assignment."""
    try:
        assignment = db.query(Assignment).filter(
            Assignment.id == request.assignment_id,
            Assignment.organization_id == current_user.organization_id
        ).first()
        if not assignment:
            raise HTTPException(status_code=404, detail="Assignment not found")

        # Check if already submitted
        existing = db.query(AssignmentSubmission).filter(
            AssignmentSubmission.assignment_id == request.assignment_id,
            AssignmentSubmission.student_id == current_user.id
        ).first()

        if existing:
            existing.score = request.score
            existing.feedback = request.feedback
            existing.submitted_at = datetime.utcnow()
            db.commit()
            db.refresh(existing)
            return existing

        submission = AssignmentSubmission(
            assignment_id=request.assignment_id,
            student_id=current_user.id,
            score=request.score,
            feedback=request.feedback
        )
        db.add(submission)
        db.commit()
        db.refresh(submission)
        return submission
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
