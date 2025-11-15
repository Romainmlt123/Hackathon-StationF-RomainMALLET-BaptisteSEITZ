"""
Integration module to send call logs from voice agent to backend webhook.
"""
import os
import httpx
from typing import List, Dict, Any, Optional
from datetime import datetime
from loguru import logger

from backend.models import CallLogCreate, TranscriptEntry


class CallLogger:
    """Helper class to build and send call logs to backend API."""
    
    def __init__(self):
        self.backend_url = os.getenv("BACKEND_API_URL", "http://localhost:8765")
        self.api_key = os.getenv("API_KEY", "your-secret-api-key-change-me")
        self.transcript: List[Dict[str, Any]] = []
        self.call_sid: Optional[str] = None
        self.started_at: Optional[datetime] = None
    
    def start_call(self, call_sid: str):
        """Initialize a new call tracking."""
        self.call_sid = call_sid
        self.started_at = datetime.now()
        self.transcript = []
        logger.info(f"📞 Started tracking call {call_sid}")
    
    def add_message(self, speaker: str, text: str):
        """Add a message to the transcript."""
        if not text.strip():
            return
        
        entry = {
            "speaker": speaker,
            "text": text,
            "timestamp": datetime.now().isoformat()
        }
        self.transcript.append(entry)
        logger.debug(f"💬 Added message from {speaker}: {text[:50]}...")
    
    def add_user_message(self, text: str):
        """Add user message to transcript."""
        self.add_message("user", text)
    
    def add_assistant_message(self, text: str):
        """Add assistant message to transcript."""
        self.add_message("assistant", text)
    
    async def send_log(
        self,
        business_id: str = "default",
        caller_number: Optional[str] = None,
        status: str = "completed",
        summary: Optional[str] = None,
        sentiment: Optional[str] = None
    ):
        """Send the call log to backend webhook."""
        if not self.call_sid or not self.started_at:
            logger.warning("⚠️ Cannot send log: call not started")
            return
        
        ended_at = datetime.now()
        duration = int((ended_at - self.started_at).total_seconds())
        
        # Build payload
        payload = CallLogCreate(
            call_sid=self.call_sid,
            business_id=business_id,
            caller_number=caller_number,
            status=status,
            started_at=self.started_at,
            ended_at=ended_at,
            duration_seconds=duration,
            transcript=[TranscriptEntry(**entry) for entry in self.transcript],
            summary=summary or self._generate_summary(),
            sentiment=sentiment or "neutral",
            metadata={}
        )
        
        # Send to backend
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.backend_url}/api/calls/log",
                    json=payload.model_dump(mode="json"),
                    headers={"X-API-Key": self.api_key},
                    timeout=10.0
                )
                response.raise_for_status()
                
                logger.info(f"✅ Call log sent successfully for {self.call_sid}")
                return response.json()
        
        except httpx.HTTPError as e:
            logger.error(f"❌ Failed to send call log: {e}")
            return None
    
    def _generate_summary(self) -> str:
        """Generate a simple summary from transcript."""
        if not self.transcript:
            return "No conversation recorded"
        
        num_messages = len(self.transcript)
        user_messages = sum(1 for msg in self.transcript if msg["speaker"] == "user")
        
        return f"Call with {num_messages} messages ({user_messages} from user)"
    
    def reset(self):
        """Reset the logger for a new call."""
        self.transcript = []
        self.call_sid = None
        self.started_at = None
