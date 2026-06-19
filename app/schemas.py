"""
Pydantic v2 schemas for request/response validation.
Every model has Create, Response, and Update variants.
Password hashes are NEVER returned in responses.
"""

import uuid
from datetime import datetime, date
from typing import Optional, List, Any
from pydantic import BaseModel, EmailStr, Field, ConfigDict


# ========== AUTH ==========

class LoginRequest(BaseModel):
    """Login request body."""
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    """Login response with JWT token."""
    access_token: str
    token_type: str = "bearer"
    role: str
    name: str


class TokenData(BaseModel):
    """Decoded JWT payload data."""
    sub: str
    role: str
    org_id: Optional[str] = None
    name: str


# ========== ORGANIZATION ==========

class OrganizationCreate(BaseModel):
    """Create organization request."""
    name: str
    plan: str = "trial"
    max_seats: int = 50


class OrganizationResponse(BaseModel):
    """Organization response."""
    id: uuid.UUID
    name: str
    plan: str
    max_seats: int
    seats_used: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class OrganizationUpdate(BaseModel):
    """Update organization request — all fields optional."""
    name: Optional[str] = None
    plan: Optional[str] = None
    max_seats: Optional[int] = None
    is_active: Optional[bool] = None


# ========== USER ==========

class UserCreate(BaseModel):
    """Create user request."""
    email: EmailStr
    password: str
    first_name: str
    last_name: Optional[str] = None
    role: str = "student"
    organization_id: Optional[uuid.UUID] = None


class UserResponse(BaseModel):
    """User response — NEVER includes password_hash."""
    id: uuid.UUID
    organization_id: Optional[uuid.UUID] = None
    email: str
    first_name: str
    last_name: Optional[str] = None
    role: str
    is_active: bool
    total_points: int
    current_streak: int
    last_login: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    """Update user request."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_active: Optional[bool] = None
    total_points: Optional[int] = None
    current_streak: Optional[int] = None


# ========== ALLOWED STUDENTS ==========

class AllowedStudentCreate(BaseModel):
    """Add student email to whitelist."""
    email: EmailStr
    role: Optional[str] = "student"


class AllowedStudentResponse(BaseModel):
    """Allowed student response."""
    id: uuid.UUID
    organization_id: uuid.UUID
    email: str
    role: str
    is_active: bool
    added_by: Optional[uuid.UUID] = None
    added_at: datetime

    model_config = {"from_attributes": True}


# ========== TENSES ==========

class TenseResponse(BaseModel):
    """Tense response."""
    id: int
    name: str
    formula: str
    explanation: Optional[str] = None
    urdu_explanation: Optional[str] = None
    example: Optional[str] = None
    mastery_percent: Optional[int] = 0
    last_practiced_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class TenseExercise(BaseModel):
    """Single tense exercise from AI."""
    sentence: str
    answer: str
    explanation: str


class TenseSubmitRequest(BaseModel):
    """Submit tense practice results."""
    mastery_percent: int = Field(ge=0, le=100)


# ========== VOCABULARY ==========

class VocabularyResponse(BaseModel):
    """Vocabulary word response."""
    id: int
    word: str
    meaning: str
    urdu_meaning: Optional[str] = None
    example_sentence: Optional[str] = None
    difficulty: Optional[str] = None

    model_config = {"from_attributes": True}


class WordOfDayResponse(BaseModel):
    """Word of the day response."""
    id: uuid.UUID
    display_date: date
    vocabulary: VocabularyResponse

    model_config = {"from_attributes": True}


# ========== ASSIGNMENTS ==========

class AssignmentCreate(BaseModel):
    """Create assignment request."""
    title: Optional[str] = None
    topic: Optional[str] = None
    description: Optional[str] = None
    max_score: int = 100
    due_date: Optional[datetime] = None



class AssignmentResponse(BaseModel):
    """Assignment response."""
    id: uuid.UUID
    organization_id: uuid.UUID
    teacher_id: uuid.UUID
    title: str
    description: Optional[str] = None
    max_score: int
    due_date: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class AssignmentSubmissionCreate(BaseModel):
    """Submit assignment request."""
    assignment_id: uuid.UUID
    score: Optional[int] = None
    feedback: Optional[str] = None


class AssignmentSubmissionResponse(BaseModel):
    """Assignment submission response."""
    id: uuid.UUID
    assignment_id: uuid.UUID
    student_id: uuid.UUID
    score: Optional[int] = None
    feedback: Optional[str] = None
    submitted_at: datetime

    model_config = {"from_attributes": True}


class AssignmentSubmissionDetail(BaseModel):
    """Detailed assignment submission for teacher dashboard."""
    id: uuid.UUID
    assignment_id: uuid.UUID
    assignment_title: str
    student_id: uuid.UUID
    student_name: str
    student_email: str
    score: Optional[int] = None
    feedback: Optional[str] = None
    submitted_at: datetime

    model_config = {"from_attributes": True}


# ========== VOICE SESSIONS ==========

class VoiceTranscribeResponse(BaseModel):
    """Response from speech-to-text transcription."""
    text: str
    language: Optional[str] = None


class VoiceRespondRequest(BaseModel):
    """Request for AI conversation response."""
    session_id: Optional[uuid.UUID] = None
    text: str
    language: Optional[str] = None
    topic: str = "Daily Life"
    difficulty: str = "intermediate"
    conversation: List[dict] = []


class VoiceRespondResponse(BaseModel):
    """AI conversation response."""
    session_id: uuid.UUID
    reply: str
    conversation: List[dict]


class VoiceEndSessionRequest(BaseModel):
    """End voice session request."""
    session_id: uuid.UUID
    conversation: List[dict]
    topic: str = "Daily Life"
    duration_seconds: int = 0


class VoiceSessionResponse(BaseModel):
    """Voice session response."""
    id: uuid.UUID
    student_id: uuid.UUID
    topic: Optional[str] = None
    grammar_score: Optional[int] = None
    vocabulary_score: Optional[int] = None
    fluency_score: Optional[int] = None
    overall_score: Optional[int] = None
    duration_seconds: Optional[int] = None
    conversation: Any = []
    report: Optional[dict] = None
    summary: Optional[str] = None
    created_at: datetime
    session_too_short: Optional[bool] = False

    model_config = {"from_attributes": True}


# ========== QUIZ ==========

class QuizGenerateRequest(BaseModel):
    """Request to generate quiz questions."""
    topic: str = "General Grammar"
    difficulty: str = "medium"
    num_questions: int = Field(default=5, ge=1, le=30)


class QuizQuestion(BaseModel):
    """Single quiz question from AI."""
    question: str
    reference_sentences: Optional[List[str]] = []
    options: List[str]
    correct_answer: str
    explanation: str


class QuizSubmitRequest(BaseModel):
    """Submit quiz results."""
    score: int
    total_questions: int


class QuizSessionResponse(BaseModel):
    """Quiz session response."""
    id: uuid.UUID
    student_id: uuid.UUID
    score: int
    total_questions: int
    created_at: datetime

    model_config = {"from_attributes": True}


# ========== PROGRESS ==========

class StudentTenseProgressResponse(BaseModel):
    """Student tense progress response."""
    id: uuid.UUID
    student_id: uuid.UUID
    tense_id: int
    mastery_percent: int
    tense: Optional[TenseResponse] = None

    model_config = {"from_attributes": True}


class StudentVocabularyResponse(BaseModel):
    """Student vocabulary tracking response."""
    id: uuid.UUID
    student_id: uuid.UUID
    vocabulary_id: int
    learned: bool
    learned_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ProgressOverview(BaseModel):
    """Full progress data for the progress page."""
    total_sessions: int
    avg_score: float
    words_learned: int
    current_streak: int
    total_points: int
    tense_mastery: List[StudentTenseProgressResponse]
    recent_quiz_scores: List[QuizSessionResponse]
    recent_voice_sessions: List[VoiceSessionResponse]


# ========== ACTIVITY LOGS ==========

class ActivityLogResponse(BaseModel):
    """Activity log response."""
    id: uuid.UUID
    user_id: Optional[uuid.UUID] = None
    action: str
    metadata_: Optional[dict] = Field(None, alias="metadata")
    created_at: datetime

    model_config = {"from_attributes": True, "populate_by_name": True}


# ========== DASHBOARD RESPONSES ==========

class StudentHomeResponse(BaseModel):
    """Student home page data."""
    user: UserResponse
    word_of_day: Optional[WordOfDayResponse] = None
    assignments: List[AssignmentResponse] = []
    submissions: List[AssignmentSubmissionResponse] = []
    stats: dict = {}



class OwnerDashboardResponse(BaseModel):
    """Owner dashboard data."""
    organization: OrganizationResponse
    total_students: int
    total_teachers: int
    students: List[AllowedStudentResponse] = []
    teachers: List[AllowedStudentResponse] = []


class TeacherDashboardResponse(BaseModel):
    """Teacher dashboard data."""
    total_students: int
    total_assignments: int
    avg_score: float
    recent_activity: List[dict] = []


class AdminDashboardResponse(BaseModel):
    """Super admin dashboard data."""
    total_organizations: int
    total_users: int
    total_students: int
    active_organizations: int
    organizations: List[OrganizationResponse] = []


class LeaderboardEntry(BaseModel):
    """Single leaderboard entry."""
    rank: int
    id: uuid.UUID
    first_name: str
    last_name: Optional[str] = None
    total_points: int
    current_streak: int

    model_config = {"from_attributes": True}


class ModalVerbResponse(BaseModel):
    id: int
    name: str
    usage: str
    urdu_explanation: Optional[str]
    positive_form: Optional[str]
    negative_form: Optional[str]
    question_form: Optional[str]
    examples: list
    order_index: int
    model_config = ConfigDict(from_attributes=True)


class ModalProgressResponse(BaseModel):
    id: int
    name: str
    attempts: int
    correct_count: int
    is_completed: bool
    mastery_percent: int
    last_practiced_at: Optional[datetime] = None


class GrammarLessonResponse(BaseModel):
    id: int
    category: str
    name: str
    urdu_explanation: Optional[str]
    rules: list
    examples: list
    order_index: int
    model_config = ConfigDict(from_attributes=True)


class GrammarProgressResponse(BaseModel):
    id: int
    name: str
    category: str
    attempts: int
    correct_count: int
    is_completed: bool
    mastery_percent: int


class ExerciseSubmit(BaseModel):
    correct_count: int
    total: int


class ExercisesResponse(BaseModel):
    exercises: list
