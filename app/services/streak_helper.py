from datetime import datetime, date, timedelta
from sqlalchemy import func, desc
from sqlalchemy.orm import Session
import logging

from app.models import User, ActivityLog

logger = logging.getLogger("speakly.streak")

def sync_user_streak(user: User, db: Session):
    """
    Dynamically calculates and updates the user's current streak based on ActivityLog.
    If active today, streak is computed backwards.
    If active yesterday (but not today), streak is computed backwards from yesterday.
    If last activity is before yesterday, streak is reset to 0.
    """
    try:
        # Query unique UTC dates where user has any activity logs
        active_dates_query = db.query(
            func.date(ActivityLog.created_at)
        ).filter(
            ActivityLog.user_id == user.id
        ).distinct().order_by(
            desc(func.date(ActivityLog.created_at))
        ).limit(60).all()
        
        # Extract date objects
        dates = []
        for d in active_dates_query:
            val = d[0]
            if val is None:
                continue
            if isinstance(val, str):
                try:
                    val = datetime.strptime(val, "%Y-%m-%d").date()
                except ValueError:
                    continue
            dates.append(val)
            
        if not dates:
            user.current_streak = 0
            db.commit()
            return
            
        today = datetime.utcnow().date()
        yesterday = today - timedelta(days=1)
        
        # Check latest activity date
        if dates[0] == today:
            # Active today, let's calculate streak going back
            streak = 1
            current_date = yesterday
            for d in dates[1:]:
                if d == current_date:
                    streak += 1
                    current_date -= timedelta(days=1)
                else:
                    break
            user.current_streak = streak
        elif dates[0] == yesterday:
            # Active yesterday (but not today yet), streak is still alive
            streak = 1
            current_date = yesterday - timedelta(days=1)
            for d in dates[1:]:
                if d == current_date:
                    streak += 1
                    current_date -= timedelta(days=1)
                else:
                    break
            user.current_streak = streak
        else:
            # Missed yesterday, streak resets to 0
            user.current_streak = 0
            
        db.commit()
        logger.info(f"Streak synced for user {user.email}: {user.current_streak} days (last active: {dates[0]})")
    except Exception as e:
        db.rollback()
        logger.warning(f"Failed to sync streak for user {user.id}: {str(e)}")
