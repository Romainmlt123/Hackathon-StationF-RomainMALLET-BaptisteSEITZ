"""
Main FastAPI server integrating Twilio voice agent and call logging backend.
"""
import os
import sys
import asyncio
from typing import Dict
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, JSONResponse
from loguru import logger

from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.frames.frames import LLMMessagesFrame, EndFrame
from pipecat.processors.aggregators.llm_response import LLMUserResponseAggregator, LLMAssistantResponseAggregator
from pipecat.services.elevenlabs.tts import ElevenLabsTTSService
from pipecat.services.elevenlabs.stt import ElevenLabsSTTService
from pipecat.services.mistral import MistralLLMService
from pipecat.transports.network.fastapi_websocket import FastAPIWebsocketTransport, FastAPIWebsocketParams
from pipecat.vad.silero import SileroVADAnalyzer

from backend.api_routes import router as api_router
from backend.call_logger import CallLogger

# Configure logger
logger.remove()
logger.add(sys.stderr, level="DEBUG")
logger.add("server.log", rotation="10 MB", level="INFO")

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Store active tasks
active_tasks: Dict[str, PipelineTask] = {}

# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Server starting...")
    yield
    logger.info("🛑 Server shutting down...")
    # Cancel all active tasks
    for task in active_tasks.values():
        task.cancel()

# Initialize FastAPI app
app = FastAPI(
    title="AI Voice Agent SaaS",
    description="Real-time voice agent with Twilio, Mistral LLM, and ElevenLabs TTS",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes for call logging
app.include_router(api_router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "active_calls": len(active_tasks)}


@app.post("/incoming-call")
async def incoming_call(request: Request):
    """
    Twilio webhook endpoint for incoming calls.
    Returns TwiML to connect to WebSocket.
    """
    # Get the public URL (you'll need to update this with your ngrok URL)
    host = request.headers.get("host", "localhost:8765")
    protocol = "wss" if request.url.scheme == "https" else "ws"
    ws_url = f"{protocol}://{host}/ws"
    
    logger.info(f"📞 Incoming call, redirecting to WebSocket: {ws_url}")
    
    # Return TwiML
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Connect>
        <Stream url="{ws_url}" />
    </Connect>
</Response>"""
    
    return Response(content=twiml, media_type="application/xml")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for Twilio audio streaming.
    Handles the complete Pipecat pipeline: STT -> LLM -> TTS
    """
    await websocket.accept()
    
    # Extract call metadata
    query_params = dict(websocket.query_params)
    stream_sid = query_params.get("streamSid", "unknown")
    call_sid = query_params.get("callSid", "unknown")
    
    logger.info(f"🎙️ WebSocket connected: call_sid={call_sid}, stream_sid={stream_sid}")
    
    # Initialize call logger
    call_logger = CallLogger()
    call_logger.start_call(call_sid)
    
    try:
        # Initialize Pipecat transport
        transport = FastAPIWebsocketTransport(
            websocket=websocket,
            params=FastAPIWebsocketParams(
                audio_out_enabled=True,
                audio_out_sample_rate=16000,
                add_wav_header=False,
                vad_enabled=True,
                vad_analyzer=SileroVADAnalyzer(),
                vad_audio_passthrough=True,
            )
        )
        
        # Initialize services
        stt = ElevenLabsSTTService(
            api_key=os.getenv("ELEVENLABS_API_KEY"),
            language="fr",  # French language
        )
        
        tts = ElevenLabsTTSService(
            api_key=os.getenv("ELEVENLABS_API_KEY"),
            voice_id=os.getenv("ELEVENLABS_VOICE_ID", "EIsgvJT3rwoPvRFG6c4n"),
        )
        
        llm = MistralLLMService(
            api_key=os.getenv("MISTRAL_API_KEY"),
            model="mistral-small-latest",
        )
        
        # Context aggregators
        user_aggregator = LLMUserResponseAggregator()
        assistant_aggregator = LLMAssistantResponseAggregator()
        
        # Build pipeline
        pipeline = Pipeline([
            transport.input(),
            stt,
            user_aggregator,
            llm,
            tts,
            transport.output(),
            assistant_aggregator,
        ])
        
        # Pipeline task
        task = PipelineTask(
            pipeline,
            params=PipelineParams(
                allow_interruptions=True,
                enable_metrics=True,
            )
        )
        
        # Store task
        active_tasks[stream_sid] = task
        
        # Event handlers
        @transport.event_handler("on_client_connected")
        async def on_client_connected(transport, client):
            logger.info(f"✅ Client connected: {stream_sid}")
            
            # Send greeting
            greeting = os.getenv("GREETING_PROMPT", "Bonjour, comment puis-je vous aider ?")
            
            # Add to call log
            call_logger.add_assistant_message(greeting)
            
            messages = [
                {
                    "role": "system",
                    "content": os.getenv("SYSTEM_PROMPT", "Vous êtes un assistant vocal IA serviable."),
                },
                {
                    "role": "assistant",
                    "content": greeting,
                }
            ]
            
            await task.queue_frames([LLMMessagesFrame(messages)])
        
        @transport.event_handler("on_client_disconnected")
        async def on_client_disconnected(transport, client):
            logger.info(f"👋 Client disconnected: {stream_sid}")
            
            # Send call log to backend
            caller_number = query_params.get("from", None)
            await call_logger.send_log(
                business_id="default",
                caller_number=caller_number,
                status="completed"
            )
            
            # Clean up
            if stream_sid in active_tasks:
                del active_tasks[stream_sid]
            
            await task.queue_frames([EndFrame()])
        
        # Capture transcript messages
        @user_aggregator.event_handler("on_user_message")
        async def on_user_message(aggregator, message):
            text = message.get("content", "")
            call_logger.add_user_message(text)
            logger.debug(f"👤 User: {text}")
        
        @assistant_aggregator.event_handler("on_assistant_message")
        async def on_assistant_message(aggregator, message):
            text = message.get("content", "")
            call_logger.add_assistant_message(text)
            logger.debug(f"🤖 Assistant: {text}")
        
        # Run pipeline
        runner = PipelineRunner()
        await runner.run(task)
    
    except WebSocketDisconnect:
        logger.warning(f"⚠️ WebSocket disconnected unexpectedly: {stream_sid}")
    
    except Exception as e:
        logger.exception(f"❌ Error in WebSocket handler: {e}")
    
    finally:
        # Clean up
        if stream_sid in active_tasks:
            del active_tasks[stream_sid]
        
        logger.info(f"🧹 Cleaned up resources for {stream_sid}")


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8765))
    
    logger.info(f"🚀 Starting server on port {port}")
    logger.info("📝 Endpoints:")
    logger.info("   - POST /incoming-call (Twilio webhook)")
    logger.info("   - WS /ws (Audio streaming)")
    logger.info("   - POST /api/calls/log (Call logging)")
    logger.info("   - GET /api/calls/{business_id} (Get calls)")
    
    uvicorn.run(
        "backend.server:app",
        host="0.0.0.0",
        port=port,
        log_level="info",
        reload=False
    )
