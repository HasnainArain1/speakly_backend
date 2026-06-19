"""
Vocabulary router — browse words, word of day, and mark as learned.
"""

from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from datetime import datetime

from app.database import get_db
from app.models import Vocabulary, WordOfDay, StudentVocabulary, User, ActivityLog
from app.schemas import VocabularyResponse, WordOfDayResponse
from app.dependencies import require_student, get_current_user

router = APIRouter()


@router.get("/", response_model=list[VocabularyResponse])
def get_vocabulary(
    level: str = Query(None, description="Filter by difficulty: easy, medium, hard"),
    search: str = Query(None, description="Search by word"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List vocabulary words with optional filtering.
    Supports filtering by difficulty level and text search.
    """
    try:
        query = db.query(Vocabulary)

        if level:
            query = query.filter(Vocabulary.difficulty == level)
        if search:
            query = query.filter(Vocabulary.word.ilike(f"%{search}%"))

        words = query.order_by(Vocabulary.word).all()
        return words
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/word-of-day", response_model=WordOfDayResponse)
def get_word_of_day(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get today's word of the day with full vocabulary details."""
    try:
        today = date.today()
        wod = db.query(WordOfDay).options(
            joinedload(WordOfDay.vocabulary)
        ).filter(
            WordOfDay.display_date == today
        ).first()

        if not wod:
            # Fallback: get the most recent word of day
            wod = db.query(WordOfDay).options(
                joinedload(WordOfDay.vocabulary)
            ).order_by(WordOfDay.display_date.desc()).first()

        if not wod:
            # Ultimate fallback: create from first vocabulary word
            first_word = db.query(Vocabulary).first()
            if first_word:
                wod = WordOfDay(vocabulary_id=first_word.id, display_date=today)
                db.add(wod)
                db.commit()
                db.refresh(wod)
                wod = db.query(WordOfDay).options(
                    joinedload(WordOfDay.vocabulary)
                ).filter(WordOfDay.id == wod.id).first()
            else:
                raise HTTPException(status_code=404, detail="No vocabulary words available")

        return wod
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{vocab_id}", response_model=VocabularyResponse)
def get_vocabulary_word(
    vocab_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a single vocabulary word by ID."""
    try:
        word = db.query(Vocabulary).filter(Vocabulary.id == vocab_id).first()
        if not word:
            raise HTTPException(status_code=404, detail="Word not found")
        return word
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{vocab_id}/mark-learned")
def mark_word_learned(
    vocab_id: int,
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db)
):
    """Mark a vocabulary word as learned and award 1 point."""
    try:
        word = db.query(Vocabulary).filter(Vocabulary.id == vocab_id).first()
        if not word:
            raise HTTPException(status_code=404, detail="Word not found")

        # Upsert student vocabulary
        sv = db.query(StudentVocabulary).filter(
            StudentVocabulary.student_id == current_user.id,
            StudentVocabulary.vocabulary_id == vocab_id
        ).first()

        if sv:
            if sv.learned:
                return {"message": "Word already learned"}
            sv.learned = True
            sv.learned_at = datetime.utcnow()
        else:
            sv = StudentVocabulary(
                student_id=current_user.id,
                vocabulary_id=vocab_id,
                learned=True,
                learned_at=datetime.utcnow()
            )
            db.add(sv)

        # Award points
        current_user.total_points += 1
        db.add(ActivityLog(
            user_id=current_user.id,
            action="vocabulary_learned",
            metadata_={"vocabulary_id": vocab_id, "word": word.word, "points_earned": 1}
        ))

        db.commit()
        return {"message": f"Word '{word.word}' marked as learned", "points_earned": 1}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
