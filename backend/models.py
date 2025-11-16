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


from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from datetime import datetime

class TranscriptEntry(BaseModel):
    """Entrée de transcription"""
    speaker: str = Field(..., description="Locuteur (user, assistant, agent)")
    text: str = Field(..., description="Texte dit")
    timestamp: Optional[str] = Field(None, description="Horodatage ISO 8601")

class ElevenLabsWebhook(BaseModel):
    """Données reçues du webhook ElevenLabs - tous les champs optionnels sauf transcript"""
    conversation_id: Optional[str] = Field(None, description="ID unique de la conversation")
    agent_id: Optional[str] = Field(None, description="ID de l'agent")
    status: Optional[str] = Field("completed", description="Statut de l'appel")
    started_at: Optional[str] = Field(None, description="Début de l'appel")
    ended_at: Optional[str] = Field(None, description="Fin de l'appel")
    transcript: Union[List[TranscriptEntry], List[str]] = Field(default_factory=list, description="Transcription")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Métadonnées")


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
