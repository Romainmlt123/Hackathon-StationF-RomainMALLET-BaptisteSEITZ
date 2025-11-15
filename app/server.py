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
        # Import necessary Pipecat components
        from pipecat.audio.vad.silero import SileroVADAnalyzer
        from pipecat.audio.vad.vad_analyzer import VADParams
        from pipecat.frames.frames import LLMRunFrame
        from pipecat.pipeline.pipeline import Pipeline
        from pipecat.pipeline.runner import PipelineRunner
        from pipecat.pipeline.task import PipelineParams, PipelineTask
        from pipecat.processors.aggregators.llm_context import LLMContext
        from pipecat.processors.aggregators.llm_response_universal import LLMContextAggregatorPair
        from pipecat.services.elevenlabs.stt import ElevenLabsRealtimeSTTService
        from pipecat.services.elevenlabs.tts import ElevenLabsTTSService
        from pipecat.services.mistral.llm import MistralLLMService
        from pipecat.transports.websocket.fastapi import FastAPIWebsocketTransport, FastAPIWebsocketParams
        
        # Create transport params with VAD
        transport_params = FastAPIWebsocketParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
            vad_analyzer=SileroVADAnalyzer(params=VADParams(stop_secs=0.2)),
        )
        
        # Create transport for this WebSocket connection
        transport = FastAPIWebsocketTransport(
            websocket=websocket,
            params=transport_params,
        )
        
        # Initialize services
        stt = ElevenLabsRealtimeSTTService(
            api_key=os.getenv("ELEVENLABS_API_KEY", ""),
            language="fr",
        )
        
        tts = ElevenLabsTTSService(
            api_key=os.getenv("ELEVENLABS_API_KEY", ""),
            voice_id=os.getenv("ELEVENLABS_VOICE_ID", ""),
        )
        
        llm = MistralLLMService(
            api_key=os.getenv("MISTRAL_API_KEY", ""),
            model="mistral-small-latest",
        )
        
        # System prompt
        system_prompt = os.getenv(
            "SYSTEM_PROMPT",
            "Tu es un assistant vocal IA intelligent et professionnel."
        )
        
        messages = [{"role": "system", "content": system_prompt}]
        context = LLMContext(messages)
        context_aggregator = LLMContextAggregatorPair(context)
        
        # Build pipeline
        pipeline = Pipeline([
            transport.input(),
            stt,
            context_aggregator.user(),
            llm,
            tts,
            transport.output(),
            context_aggregator.assistant(),
        ])
        
        # Create task
        task = PipelineTask(
            pipeline,
            params=PipelineParams(
                enable_metrics=True,
                enable_usage_metrics=True,
            ),
        )
        
        # Event handlers
        @transport.event_handler("on_client_connected")
        async def on_client_connected(transport, client):
            logger.info(f"📞 Client connected to pipeline")
            greeting = os.getenv("GREETING_PROMPT", "Salue l'appelant brievement.")
            messages.append({"role": "system", "content": greeting})
            await task.queue_frames([LLMRunFrame()])
        
        @transport.event_handler("on_client_disconnected")
        async def on_client_disconnected(transport, client):
            logger.info(f"📴 Client disconnected from pipeline")
            await task.cancel()
        
        # Run the pipeline
        runner = PipelineRunner(handle_sigint=False)
        await runner.run(task)
        
    except Exception as e:
        logger.exception(f"❌ Error in WebSocket handler: {e}")
        raise
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
