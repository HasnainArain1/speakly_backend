"""
Speakly API — FastAPI application entry point.
AI-powered English Grammar Tutor for Pakistani coaching centers.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.database import engine
from app.logging_config import setup_logging
from app.routers import (
    auth, students, teachers, owners,
    admin, voice, quiz, tenses, vocabulary, progress,
    modal_verbs, grammar_lessons
)
from app.limiter import limiter
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

# Initialize structured logging
setup_logging()
logger = logging.getLogger("speakly.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown events."""
    # Startup
    logger.info("Speakly API starting up...")
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("Database connection verified OK")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
    yield
    # Shutdown
    logger.info("Speakly API shutting down...")


app = FastAPI(
    title="Speakly API",
    description="AI-powered English Grammar Tutor SaaS for Pakistani coaching centers",
    version="1.0.0",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS — allow frontend dev server and common origins
import os

allowed_origins = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
]

env_origins = os.getenv("ALLOWED_ORIGINS")
if env_origins:
    allowed_origins.extend([origin.strip() for origin in env_origins.split(",") if origin.strip()])

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register all API routers
app.include_router(auth.router,       prefix="/api/auth",       tags=["Auth"])
app.include_router(students.router,   prefix="/api/students",   tags=["Students"])
app.include_router(teachers.router,   prefix="/api/teacher",    tags=["Teacher"])
app.include_router(owners.router,     prefix="/api/owner",      tags=["Owner"])
app.include_router(admin.router,      prefix="/api/admin",      tags=["Admin"])
app.include_router(voice.router,      prefix="/api/voice",      tags=["Voice"])
app.include_router(quiz.router,       prefix="/api/quiz",       tags=["Quiz"])
app.include_router(tenses.router,     prefix="/api/tenses",     tags=["Tenses"])
app.include_router(vocabulary.router, prefix="/api/vocabulary", tags=["Vocabulary"])
app.include_router(progress.router,   prefix="/api/progress",   tags=["Progress"])
app.include_router(modal_verbs.router, prefix="/api/modal-verbs", tags=["Modal Verbs"])
app.include_router(grammar_lessons.router, prefix="/api/grammar-lessons", tags=["Grammar Lessons"])


@app.get("/", tags=["Health"])
def root():
    """Health check endpoint."""
    return {"status": "ok", "message": "Speakly API is running", "version": "1.0.0"}


@app.get("/health", tags=["Health"])
def health_check():
    """
    Deep health check — verifies database connectivity.
    Used by monitoring tools and load balancers.
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "unhealthy", "database": str(e)}
