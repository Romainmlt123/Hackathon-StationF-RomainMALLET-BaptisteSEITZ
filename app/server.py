#
# Hackathon StationF - FastAPI server for Twilio webhook
#
# This file creates a FastAPI server that Twilio can call via webhook
# when an inbound call arrives. It spawns a bot session using the
# Pipecat runner for each call.
#

import os
from fastapi import FastAPI, WebSocket, Request
from fastapi.responses import Response
from loguru import logger
from dotenv import load_dotenv

load_dotenv(override=True)

app = FastAPI(title="Realtime Voice Agent - Twilio Webhook")


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "service": "voice-agent"}


@app.post("/incoming-call")
async def incoming_call(request: Request):
    """Twilio webhook endpoint for incoming calls.
    
    Twilio calls this endpoint when a phone call arrives.
    We return TwiML that tells Twilio to connect the call to our WebSocket.
    """
    # Get the request form data
    form_data = await request.form()
    from_number = form_data.get("From", "unknown")
    to_number = form_data.get("To", "unknown")
    call_sid = form_data.get("CallSid", "unknown")
    
    logger.info(f"📞 Incoming call: {from_number} → {to_number} (CallSid: {call_sid})")
    
    # Get the public URL (from env or construct from request)
    ws_base_url = os.getenv("PUBLIC_WS_URL", f"wss://{request.headers.get('host', 'localhost')}")
    ws_url = f"{ws_base_url}/ws/{call_sid}"
    
    # Return TwiML to connect the call to our WebSocket
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Connect>
        <Stream url="{ws_url}">
            <Parameter name="callSid" value="{call_sid}"/>
        </Stream>
    </Connect>
</Response>"""
    
    return Response(content=twiml, media_type="application/xml")


@app.websocket("/ws/{stream_sid}")
async def websocket_endpoint(websocket: WebSocket, stream_sid: str):
    """WebSocket endpoint for Twilio Media Streams.
    
    This is where the actual audio streaming happens.
    Twilio connects to this endpoint and sends/receives audio data.
    """
    await websocket.accept()
    logger.info(f"🔌 WebSocket connected: {stream_sid}")
    
    try:
        # Import the bot runner from our main module
        from app.main import run_bot
        from pipecat.runner.types import RunnerArguments
        from pipecat.transports.websocket.fastapi import FastAPIWebsocketTransport
        from pipecat.audio.vad.silero import SileroVADAnalyzer
        from pipecat.audio.vad.vad_analyzer import VADParams
        from pipecat.audio.turn.smart_turn.local_smart_turn_v3 import LocalSmartTurnAnalyzerV3
        from pipecat.audio.turn.smart_turn.base_smart_turn import SmartTurnParams
        
        # Create transport for this WebSocket connection
        transport = FastAPIWebsocketTransport(
            websocket=websocket,
            params={
                "audio_in_enabled": True,
                "audio_out_enabled": True,
                "vad_analyzer": SileroVADAnalyzer(params=VADParams(stop_secs=0.2)),
                "turn_analyzer": LocalSmartTurnAnalyzerV3(params=SmartTurnParams()),
            }
        )
        
        # Create runner arguments
        runner_args = RunnerArguments(
            handle_sigint=False,
            pipeline_idle_timeout_secs=300,  # 5 minutes
        )
        
        # Run the bot for this call
        await run_bot(transport, runner_args)
        
    except Exception as e:
        logger.exception(f"❌ Error in WebSocket handler: {e}")
    finally:
        logger.info(f"📴 WebSocket disconnected: {stream_sid}")


if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8765"))
    
    logger.info(f"🚀 Starting Twilio webhook server on {host}:{port}")
    logger.info(f"📋 Webhook URL: http://{host}:{port}/incoming-call")
    logger.info(f"🔌 WebSocket URL: ws://{host}:{port}/ws/{{stream_sid}}")
    
    uvicorn.run(app, host=host, port=port)
