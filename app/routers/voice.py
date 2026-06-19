"""
Voice router — speech-to-text, AI conversation, and session reports.
"""

import uuid
import re
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request
from sqlalchemy.orm import Session
from app.limiter import limiter

from app.database import get_db
from app.models import VoiceSession, User, ActivityLog
from app.schemas import (
    VoiceTranscribeResponse, VoiceRespondRequest, VoiceRespondResponse,
    VoiceEndSessionRequest, VoiceSessionResponse
)
from app.dependencies import require_student
from app.services.groq_service import (
    transcribe_audio, get_conversation_response,
    generate_end_session_report
)

router = APIRouter()


LANG_MAP = {
    "ur": "Urdu",
    "urdu": "Urdu",
    "pa": "Punjabi",
    "punjabi": "Punjabi",
    "sd": "Sindhi",
    "sindhi": "Sindhi",
    "ps": "Pashto",
    "pashto": "Pashto",
    "hi": "Hindi",
    "hindi": "Hindi",
    "es": "Spanish",
    "spanish": "Spanish",
    "fr": "French",
    "french": "French",
    "de": "German",
    "german": "German",
    "zh": "Chinese",
    "chinese": "Chinese",
    "ar": "Arabic",
    "arabic": "Arabic",
    "fa": "Persian",
    "persian": "Persian",
    "tr": "Turkish",
    "turkish": "Turkish",
    "ru": "Russian",
    "russian": "Russian",
    "ja": "Japanese",
    "japanese": "Japanese",
    "ko": "Korean",
    "korean": "Korean",
    "it": "Italian",
    "italian": "Italian",
    "pt": "Portuguese",
    "portuguese": "Portuguese",
}


def is_english_language(lang: str) -> bool:
    if not lang:
        return True
    lang_lower = lang.lower().strip()
    return lang_lower in {"english", "en", "eng"}


def contains_non_english_script(text: str) -> bool:
    # Match Perso-Arabic (Urdu, Punjabi, Pashto, Arabic, Sindhi) and Devanagari (Hindi)
    pattern = r"[\u0600-\u06FF\u0750-\u077F\uFB50-\uFDFF\uFE70-\uFEFF\u0900-\u097F]"
    return bool(re.search(pattern, text))


@router.post("/transcribe", response_model=VoiceTranscribeResponse)
@limiter.limit("20/minute")
async def transcribe_voice(
    request: Request,
    audio: UploadFile = File(...),
    current_user: User = Depends(require_student)
):
    """Transcribe uploaded audio to text using Groq Whisper."""
    try:
        audio_data = await audio.read()
        res = await transcribe_audio(audio_data)
        return VoiceTranscribeResponse(text=res["text"], language=res["language"])
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Transcription failed: {str(e)}"
        )


@router.post("/respond", response_model=VoiceRespondResponse)
@limiter.limit("30/minute")
async def voice_respond(
    request: Request,
    payload: VoiceRespondRequest,
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db)
):
    """Get AI tutor response. Creates session if none exists."""
    try:
        conversation = payload.conversation.copy()
        conversation.append({"role": "student", "content": payload.text})

        # Check if the user is speaking a language other than English
        is_english = True
        if payload.language and not is_english_language(payload.language):
            is_english = False
        elif contains_non_english_script(payload.text):
            is_english = False

        if not is_english:
            lang_name = "another language"
            if payload.language:
                lang_lower = payload.language.lower().strip()
                lang_name = LANG_MAP.get(lang_lower, payload.language.capitalize())
            ai_reply = f"I noticed you are speaking {lang_name}. Let's try to practice in English! How would you say that in English?"
        else:
            ai_reply = await get_conversation_response(
                conversation=conversation,
                topic=payload.topic,
                difficulty=payload.difficulty
            )
        conversation.append({"role": "ai", "content": ai_reply})

        session_id = payload.session_id
        if not session_id:
            session = VoiceSession(
                student_id=current_user.id,
                topic=payload.topic,
                conversation=conversation
            )
            db.add(session)
            db.commit()
            db.refresh(session)
            session_id = session.id
        else:
            session = db.query(VoiceSession).filter(
                VoiceSession.id == session_id,
                VoiceSession.student_id == current_user.id
            ).first()
            if session:
                session.conversation = conversation
                db.commit()

        return VoiceRespondResponse(
            session_id=session_id,
            reply=ai_reply,
            conversation=conversation
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Voice response failed: {str(e)}"
        )


@router.post("/end-session", response_model=VoiceSessionResponse)
@limiter.limit("10/minute")
async def end_voice_session(
    request: Request,
    payload: VoiceEndSessionRequest,
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db)
):
    """End session, generate AI report, save scores, award points."""
    try:
        session = db.query(VoiceSession).filter(
            VoiceSession.id == payload.session_id,
            VoiceSession.student_id == current_user.id
        ).first()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        session_too_short = payload.duration_seconds < 480

        # Merge or pick the most complete conversation list available
        conversation_to_use = payload.conversation
        if session.conversation and len(session.conversation) > len(payload.conversation):
            conversation_to_use = session.conversation

        if session_too_short:
            session.conversation = conversation_to_use
            session.report = None
            session.grammar_score = None
            session.vocabulary_score = None
            session.fluency_score = None
            session.overall_score = None
            session.duration_seconds = payload.duration_seconds
            session.summary = ""
            db.commit()
            db.refresh(session)
        else:
            report = await generate_end_session_report(conversation_to_use)

            session.conversation = conversation_to_use
            session.report = report
            session.grammar_score = report.get("grammar_score", 0)
            session.vocabulary_score = report.get("vocabulary_score", 0)
            session.fluency_score = report.get("fluency_score", 0)
            session.overall_score = report.get("overall_score", 0)
            session.duration_seconds = payload.duration_seconds
            session.summary = report.get("next_session_goal", "")

            current_user.total_points += 10
            db.add(ActivityLog(
                user_id=current_user.id,
                action="voice_session_completed",
                metadata_={
                    "session_id": str(session.id),
                    "overall_score": session.overall_score,
                    "points_earned": 10
                }
            ))
            db.commit()
            db.refresh(session)

        return {
            "id": session.id,
            "student_id": session.student_id,
            "topic": session.topic,
            "grammar_score": session.grammar_score,
            "vocabulary_score": session.vocabulary_score,
            "fluency_score": session.fluency_score,
            "overall_score": session.overall_score,
            "duration_seconds": session.duration_seconds,
            "conversation": session.conversation,
            "report": session.report,
            "summary": session.summary,
            "created_at": session.created_at,
            "session_too_short": session_too_short
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"End session failed: {str(e)}"
        )
