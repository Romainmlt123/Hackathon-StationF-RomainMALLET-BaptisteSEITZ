"""
Database connection and operations for Supabase PostgreSQL.
"""
import os
from typing import List, Optional
from datetime import datetime
from supabase import create_client, Client
from loguru import logger

from backend.models import CallLogCreate, CallLogResponse


class Database:
    """Async-compatible Supabase database client."""
    
    def __init__(self):
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        
        if not supabase_url or not supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set")
        
        self.client: Client = create_client(supabase_url, supabase_key)
    
    async def create_call_log(self, call_data: CallLogCreate) -> CallLogResponse:
        """Insert a new call log into the database."""
        try:
            # Convert pydantic model to dict
            data = call_data.dict()
            
            # Convert transcript list to JSONB format
            data["transcript"] = [t.dict() for t in call_data.transcript]
            
            # Insert into Supabase
            result = self.client.table("call_logs").insert(data).execute()
            
            if not result.data:
                raise Exception("No data returned from insert")
            
            logger.info(f"Created call log: {result.data[0]['id']}")
            return CallLogResponse(**result.data[0])
        
        except Exception as e:
            logger.exception(f"Failed to create call log: {e}")
            raise
    
    async def get_call_log(self, call_id: str) -> Optional[CallLogResponse]:
        """Get a single call log by ID."""
        try:
            result = self.client.table("call_logs").select("*").eq("id", call_id).execute()
            
            if not result.data:
                return None
            
            return CallLogResponse(**result.data[0])
        
        except Exception as e:
            logger.exception(f"Failed to get call log {call_id}: {e}")
            return None
    
    async def get_calls_by_business(
        self,
        business_id: str,
        page: int = 1,
        page_size: int = 50,
        status: Optional[str] = None
    ) -> tuple[List[CallLogResponse], int]:
        """Get paginated call logs for a business."""
        try:
            query = self.client.table("call_logs").select("*", count="exact")
            query = query.eq("business_id", business_id)
            
            if status:
                query = query.eq("status", status)
            
            # Order by most recent first
            query = query.order("started_at", desc=True)
            
            # Pagination
            offset = (page - 1) * page_size
            query = query.range(offset, offset + page_size - 1)
            
            result = query.execute()
            
            calls = [CallLogResponse(**row) for row in result.data]
            total = result.count or 0
            
            return calls, total
        
        except Exception as e:
            logger.exception(f"Failed to get calls for business {business_id}: {e}")
            return [], 0
    
    async def update_call_status(
        self,
        call_sid: str,
        status: str,
        ended_at: Optional[datetime] = None,
        summary: Optional[str] = None
    ) -> bool:
        """Update call status and optionally end time and summary."""
        try:
            data = {"status": status}
            
            if ended_at:
                data["ended_at"] = ended_at.isoformat()
            
            if summary:
                data["summary"] = summary
            
            result = self.client.table("call_logs").update(data).eq("call_sid", call_sid).execute()
            
            return bool(result.data)
        
        except Exception as e:
            logger.exception(f"Failed to update call {call_sid}: {e}")
            return False


# Singleton instance
_db: Optional[Database] = None


def get_db() -> Database:
    """Get or create database singleton."""
    global _db
    if _db is None:
        _db = Database()
    return _db
