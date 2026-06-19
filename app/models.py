"""
SQLAlchemy 2.x ORM models for all 14 Speakly database tables.
Matches the speakly_schema_v3.sql exactly.
"""

import uuid
from datetime import datetime, date
from typing import Optional, List

from sqlalchemy import (
    String, Integer, Boolean, Text, DateTime, Date,
    ForeignKey, JSON, CheckConstraint, UniqueConstraint, Index
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Organization(Base):
    """Coaching center / organization model."""
    __tablename__ = "organizations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    plan: Mapped[str] = mapped_column(
        String(20), nullable=False, default="trial"
    )
    max_seats: Mapped[int] = mapped_column(Integer, nullable=False, default=50)
    seats_used: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    users: Mapped[List["User"]] = relationship("User", back_populates="organization")
    allowed_students: Mapped[List["AllowedStudent"]] = relationship(
        "AllowedStudent", back_populates="organization"
    )
    assignments: Mapped[List["Assignment"]] = relationship(
        "Assignment", back_populates="organization"
    )

    __table_args__ = (
        CheckConstraint("plan IN ('trial','starter','growth','academy')", name="ck_org_plan"),
        CheckConstraint("max_seats > 0", name="ck_org_max_seats"),
        CheckConstraint("seats_used >= 0", name="ck_org_seats_used"),
    )


class User(Base):
    """User model — students, teachers, owners, and super admins."""
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="SET NULL"),
        nullable=True
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    total_points: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    current_streak: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    organization: Mapped[Optional["Organization"]] = relationship(
        "Organization", back_populates="users"
    )
    voice_sessions: Mapped[List["VoiceSession"]] = relationship(
        "VoiceSession", back_populates="student"
    )
    quiz_sessions: Mapped[List["QuizSession"]] = relationship(
        "QuizSession", back_populates="student"
    )
    tense_progress: Mapped[List["StudentTenseProgress"]] = relationship(
        "StudentTenseProgress", back_populates="student"
    )
    student_vocabulary: Mapped[List["StudentVocabulary"]] = relationship(
        "StudentVocabulary", back_populates="student"
    )
    activity_logs: Mapped[List["ActivityLog"]] = relationship(
        "ActivityLog", back_populates="user"
    )

    __table_args__ = (
        CheckConstraint(
            "role IN ('super_admin','owner','teacher','student')",
            name="ck_user_role"
        ),
        Index("idx_users_org", "organization_id"),
        Index("idx_users_role", "role"),
    )


class AllowedStudent(Base):
    """Email whitelist for seat control — determines who can register."""
    __tablename__ = "allowed_students"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="student")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    added_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    added_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization", back_populates="allowed_students"
    )

    __table_args__ = (
        UniqueConstraint("organization_id", "email", name="uq_allowed_org_email"),
        Index("idx_allowed_org", "organization_id"),
        Index("idx_allowed_email", "email"),
    )


class Tense(Base):
    """English tense reference data — 12 tenses with formulas and Urdu explanations."""
    __tablename__ = "tenses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    formula: Mapped[str] = mapped_column(String(200), nullable=False)
    explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    urdu_explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    example: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )


class Vocabulary(Base):
    """Vocabulary word bank with English and Urdu meanings."""
    __tablename__ = "vocabulary"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    word: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    meaning: Mapped[str] = mapped_column(Text, nullable=False)
    urdu_meaning: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    example_sentence: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    difficulty: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )

    __table_args__ = (
        CheckConstraint(
            "difficulty IN ('easy','medium','hard')",
            name="ck_vocab_difficulty"
        ),
        Index("idx_vocab_word", "word"),
    )


class Assignment(Base):
    """Teacher-created assignments for students."""
    __tablename__ = "assignments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False
    )
    teacher_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    max_score: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization", back_populates="assignments"
    )
    teacher: Mapped["User"] = relationship("User")
    submissions: Mapped[List["AssignmentSubmission"]] = relationship(
        "AssignmentSubmission", back_populates="assignment"
    )

    __table_args__ = (
        Index("idx_assignments_teacher", "teacher_id"),
    )


class AssignmentSubmission(Base):
    """Student submissions for assignments."""
    __tablename__ = "assignment_submissions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    assignment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("assignments.id", ondelete="CASCADE"),
        nullable=False
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )

    # Relationships
    assignment: Mapped["Assignment"] = relationship(
        "Assignment", back_populates="submissions"
    )
    student: Mapped["User"] = relationship("User")

    __table_args__ = (
        UniqueConstraint("assignment_id", "student_id", name="uq_submission_assignment_student"),
    )


class VoiceSession(Base):
    """AI voice practice session with conversation history and report."""
    __tablename__ = "voice_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    topic: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    grammar_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    vocabulary_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    fluency_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    overall_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    duration_seconds: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    conversation: Mapped[dict] = mapped_column(JSONB, nullable=False, default=list)
    report: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )

    # Relationships
    student: Mapped["User"] = relationship("User", back_populates="voice_sessions")

    __table_args__ = (
        CheckConstraint("grammar_score BETWEEN 0 AND 100", name="ck_voice_grammar"),
        CheckConstraint("vocabulary_score BETWEEN 0 AND 100", name="ck_voice_vocab"),
        CheckConstraint("fluency_score BETWEEN 0 AND 100", name="ck_voice_fluency"),
        CheckConstraint("overall_score BETWEEN 0 AND 100", name="ck_voice_overall"),
        Index("idx_voice_student", "student_id"),
    )


class QuizSession(Base):
    """Grammar quiz session results."""
    __tablename__ = "quiz_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    total_questions: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )

    # Relationships
    student: Mapped["User"] = relationship("User", back_populates="quiz_sessions")

    __table_args__ = (
        Index("idx_quiz_student", "student_id"),
    )


class StudentTenseProgress(Base):
    """Tracks student mastery percentage for each tense."""
    __tablename__ = "student_tense_progress"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    tense_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tenses.id", ondelete="CASCADE"),
        nullable=False
    )
    mastery_percent: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    last_practiced_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )

    # Relationships
    student: Mapped["User"] = relationship("User", back_populates="tense_progress")
    tense: Mapped["Tense"] = relationship("Tense")

    __table_args__ = (
        UniqueConstraint("student_id", "tense_id", name="uq_student_tense"),
        CheckConstraint("mastery_percent BETWEEN 0 AND 100", name="ck_mastery_pct"),
    )


class StudentVocabulary(Base):
    """Tracks which vocabulary words a student has learned."""
    __tablename__ = "student_vocabulary"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    vocabulary_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("vocabulary.id", ondelete="CASCADE"),
        nullable=False
    )
    learned: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    learned_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    student: Mapped["User"] = relationship("User", back_populates="student_vocabulary")
    vocabulary: Mapped["Vocabulary"] = relationship("Vocabulary")

    __table_args__ = (
        UniqueConstraint("student_id", "vocabulary_id", name="uq_student_vocab"),
    )


class WordOfDay(Base):
    """Daily featured vocabulary word."""
    __tablename__ = "word_of_day"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    vocabulary_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("vocabulary.id", ondelete="CASCADE"),
        nullable=False
    )
    display_date: Mapped[date] = mapped_column(Date, unique=True, nullable=False)

    # Relationships
    vocabulary: Mapped["Vocabulary"] = relationship("Vocabulary")


class ActivityLog(Base):
    """Tracks all user activities for points and analytics."""
    __tablename__ = "activity_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True
    )
    action: Mapped[str] = mapped_column(String(255), nullable=False)
    metadata_: Mapped[Optional[dict]] = mapped_column(
        "metadata", JSONB, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )

    # Relationships
    user: Mapped[Optional["User"]] = relationship("User", back_populates="activity_logs")

    __table_args__ = (
        Index("idx_activity_user", "user_id"),
    )


class ModalVerb(Base):
    __tablename__ = "modal_verbs"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    usage: Mapped[str] = mapped_column(String(200))
    urdu_explanation: Mapped[Optional[str]] = mapped_column(Text)
    positive_form: Mapped[Optional[str]] = mapped_column(Text)
    negative_form: Mapped[Optional[str]] = mapped_column(Text)
    question_form: Mapped[Optional[str]] = mapped_column(Text)
    examples: Mapped[dict] = mapped_column(JSONB, default=list)
    order_index: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # Relationship to progress
    progress: Mapped[List["StudentModalProgress"]] = relationship("StudentModalProgress", back_populates="modal_verb")


class StudentModalProgress(Base):
    __tablename__ = "student_modal_progress"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    modal_verb_id: Mapped[int] = mapped_column(ForeignKey("modal_verbs.id"))
    attempts: Mapped[int] = mapped_column(default=0)
    correct_count: Mapped[int] = mapped_column(default=0)
    is_completed: Mapped[bool] = mapped_column(default=False)
    last_practiced_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    # Relationships
    modal_verb: Mapped["ModalVerb"] = relationship("ModalVerb", back_populates="progress")


class GrammarLesson(Base):
    __tablename__ = "grammar_lessons"
    id: Mapped[int] = mapped_column(primary_key=True)
    category: Mapped[str] = mapped_column(String(100))
    name: Mapped[str] = mapped_column(String(200))
    urdu_explanation: Mapped[Optional[str]] = mapped_column(Text)
    rules: Mapped[dict] = mapped_column(JSONB, default=list)
    examples: Mapped[dict] = mapped_column(JSONB, default=list)
    order_index: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # Relationship to progress
    progress: Mapped[List["StudentGrammarProgress"]] = relationship("StudentGrammarProgress", back_populates="lesson")


class StudentGrammarProgress(Base):
    __tablename__ = "student_grammar_progress"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    lesson_id: Mapped[int] = mapped_column(ForeignKey("grammar_lessons.id"))
    attempts: Mapped[int] = mapped_column(default=0)
    correct_count: Mapped[int] = mapped_column(default=0)
    is_completed: Mapped[bool] = mapped_column(default=False)
    last_practiced_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    # Relationships
    lesson: Mapped["GrammarLesson"] = relationship("GrammarLesson", back_populates="progress")
