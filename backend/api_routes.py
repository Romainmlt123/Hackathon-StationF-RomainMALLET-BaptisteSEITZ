"""
FastAPI routes for call logging and retrieval.
"""
from fastapi import APIRouter, HTTPException, Header, Query
from typing import Optional
from loguru import logger

from backend.models import CallLogCreate, CallLogResponse, CallLogList
from backend.database import get_db


router = APIRouter(prefix="/api/calls", tags=["calls"])


# Simple API key authentication
def verify_api_key(x_api_key: str = Header(...)) -> bool:
    """Verify API key from header."""
    import os
    expected_key = os.getenv("API_KEY", "your-secret-api-key-change-me")
    
    if x_api_key != expected_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    return True


@router.post("/log", response_model=CallLogResponse, status_code=201)
async def log_call(
    call_data: CallLogCreate,
    authenticated: bool = Header(None, include_in_schema=False, alias="x-api-key")
):
    """
    Webhook endpoint to log a completed or ongoing call.
    
    Called by the voice agent at the end of each call.
    Requires `X-API-Key` header for authentication.
    """
    # Verify API key
    verify_api_key(authenticated)
    
    try:
        db = get_db()
        result = await db.create_call_log(call_data)
        
        logger.info(f"✅ Logged call {call_data.call_sid} for business {call_data.business_id}")
        
        return result
    
    except Exception as e:
        logger.exception(f"❌ Failed to log call: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{business_id}", response_model=CallLogList)
async def get_business_calls(
    business_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    status: Optional[str] = Query(None),
    authenticated: bool = Header(None, include_in_schema=False, alias="x-api-key")
):
    """
    Get paginated call logs for a specific business.
    
    Requires `X-API-Key` header for authentication.
    """
    verify_api_key(authenticated)
    
    try:
        db = get_db()
        calls, total = await db.get_calls_by_business(business_id, page, page_size, status)
        
        return CallLogList(
            total=total,
            calls=calls,
            page=page,
            page_size=page_size
        )
    
    except Exception as e:
        logger.exception(f"❌ Failed to get calls for business {business_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/call/{call_id}", response_model=CallLogResponse)
async def get_call_details(
    call_id: str,
    authenticated: bool = Header(None, include_in_schema=False, alias="x-api-key")
):
    """
    Get detailed information about a specific call.
    
    Requires `X-API-Key` header for authentication.
    """
    verify_api_key(authenticated)
    
    try:
        db = get_db()
        call = await db.get_call_log(call_id)
        
        if not call:
            raise HTTPException(status_code=404, detail="Call not found")
        
        return call
    
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"❌ Failed to get call {call_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
