"""
Backend models for call logs and API schemas.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class CallStatus(str, Enum):
    """Status of a call."""
    in_progress = "in_progress"
    completed = "completed"
    failed = "failed"
    no_answer = "no_answer"
    busy = "busy"


class Sentiment(str, Enum):
    """Sentiment analysis of the call."""
    positive = "positive"
    neutral = "neutral"
    negative = "negative"


class TranscriptEntry(BaseModel):
    """Single message in a conversation transcript."""
    speaker: str = Field(..., description="'user' or 'assistant'")
    text: str = Field(..., description="Transcribed or generated text")
    timestamp: datetime = Field(..., description="When this was said")


class CallLogCreate(BaseModel):
    """Payload received from the voice agent webhook."""
    call_sid: str = Field(..., min_length=30, max_length=34)
    business_id: str = Field(..., description="UUID of the business")
    business_name: Optional[str] = None
    caller_number: str
    twilio_number: str
    started_at: datetime
    ended_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    status: CallStatus = CallStatus.completed
    transcript: List[TranscriptEntry] = Field(default_factory=list)
    summary: Optional[str] = None
    sentiment: Optional[Sentiment] = Sentiment.neutral
    language: str = "fr"
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class CallLogResponse(CallLogCreate):
    """Response model with database ID."""
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class CallLogList(BaseModel):
    """Paginated list of call logs."""
    total: int
    calls: List[CallLogResponse]
    page: int
    page_size: int
