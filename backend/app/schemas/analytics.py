from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class AnalyticsOverview(BaseModel):
    total_questions: int
    resolved_by_ai: int
    resolved_percentage: float
    escalated_questions: int
    escalated_percentage: float
    low_confidence_questions: int
    active_policies: int
    total_users: int


class TopicStat(BaseModel):
    topic: str
    count: int
    percentage: float


class QuestionStat(BaseModel):
    question: str
    count: int
    resolved: bool
    requires_hr: bool
    region: str


class FeedbackStat(BaseModel):
    total_feedback: int
    positive_count: int
    negative_count: int
    positive_percentage: float
    reasons_breakdown: Dict[str, int]


class RegionStat(BaseModel):
    region: str
    count: int


class UnansweredQuestionStat(BaseModel):
    id: str
    question: str
    region: str
    confidence: str
    created_at: str
    escalated: bool

