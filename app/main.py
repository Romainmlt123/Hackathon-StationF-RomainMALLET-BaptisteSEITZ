#
# Hackathon StationF - Realtime Voice Agent
# Based on Pipecat official examples
#
# This bot handles inbound Twilio calls with:
# - ElevenLabs STT (speech-to-text)
# - Mistral LLM (language model)
# - ElevenLabs TTS (text-to-speech streaming)
#

import os

from dotenv import load_dotenv
from loguru import logger

from pipecat.audio.turn.smart_turn.base_smart_turn import SmartTurnParams
from pipecat.audio.turn.smart_turn.local_smart_turn_v3 import LocalSmartTurnAnalyzerV3
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.audio.vad.vad_analyzer import VADParams
from pipecat.frames.frames import LLMRunFrame
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.processors.aggregators.llm_response_universal import LLMContextAggregatorPair
from pipecat.runner.types import RunnerArguments
from pipecat.runner.utils import create_transport
from pipecat.services.elevenlabs.stt import ElevenLabsRealtimeSTTService
from pipecat.services.elevenlabs.tts import ElevenLabsTTSService
from pipecat.services.mistral.llm import MistralLLMService
from pipecat.transports.base_transport import BaseTransport, TransportParams
from pipecat.transports.daily.transport import DailyParams
from pipecat.transports.websocket.fastapi import FastAPIWebsocketParams

load_dotenv(override=True)


# Transport configuration for different platforms
# For Twilio: use FastAPIWebsocketParams
# For Daily: use DailyParams
# For generic WebRTC: use TransportParams
transport_params = {
    "daily": lambda: DailyParams(
        audio_in_enabled=True,
        audio_out_enabled=True,
        vad_analyzer=SileroVADAnalyzer(params=VADParams(stop_secs=0.2)),
        turn_analyzer=LocalSmartTurnAnalyzerV3(params=SmartTurnParams()),
    ),
    "twilio": lambda: FastAPIWebsocketParams(
        audio_in_enabled=True,
        audio_out_enabled=True,
        vad_analyzer=SileroVADAnalyzer(params=VADParams(stop_secs=0.2)),
        turn_analyzer=LocalSmartTurnAnalyzerV3(params=SmartTurnParams()),
    ),
    "webrtc": lambda: TransportParams(
        audio_in_enabled=True,
        audio_out_enabled=True,
        vad_analyzer=SileroVADAnalyzer(params=VADParams(stop_secs=0.2)),
        turn_analyzer=LocalSmartTurnAnalyzerV3(params=SmartTurnParams()),
    ),
}


async def run_bot(transport: BaseTransport, runner_args: RunnerArguments):
    """Main bot logic: assembles the voice pipeline with STT -> LLM -> TTS.
    
    This function is called when a client connects (e.g., Twilio call arrives).
    """
    logger.info("Starting Realtime Voice Agent for incoming call")

    # ========== 1. Speech-to-Text (STT) ==========
    # Using ElevenLabs Realtime STT for low-latency transcription
    stt = ElevenLabsRealtimeSTTService(
        api_key=os.getenv("ELEVENLABS_API_KEY", ""),
        language="fr",  # Français par défaut
    )

    # ========== 2. Text-to-Speech (TTS) ==========
    # Using ElevenLabs TTS with streaming for realtime audio generation
    tts = ElevenLabsTTSService(
        api_key=os.getenv("ELEVENLABS_API_KEY", ""),
        voice_id=os.getenv("ELEVENLABS_VOICE_ID", ""),
    )

    # ========== 3. Language Model (LLM) ==========
    # Using Mistral LLM via API for natural conversation
    llm = MistralLLMService(
        api_key=os.getenv("MISTRAL_API_KEY", ""),
        model="mistral-small-latest",  # ou "mistral-medium-latest"
    )

    # ========== 4. System Prompt & Context ==========
    # Define the bot's personality and behavior
    system_prompt = os.getenv(
        "SYSTEM_PROMPT",
        """Tu es un assistant vocal IA intelligent et professionnel pour l'accueil téléphonique d'une entreprise.

Tu dois :
- Accueillir chaleureusement l'appelant
- Comprendre sa demande
- Répondre de manière concise et claire
- Orienter l'appelant si nécessaire

Ta réponse sera vocalisée, évite donc les emojis, listes à puces, ou caractères spéciaux.
Reste naturel et conversationnel.""",
    )

    messages = [
        {
            "role": "system",
            "content": system_prompt,
        },
    ]

    # LLM Context manages conversation history
    context = LLMContext(messages)
    context_aggregator = LLMContextAggregatorPair(context)

    # ========== 5. Build the Pipeline ==========
    # Pipeline: audio input -> STT -> context -> LLM -> TTS -> audio output
    pipeline = Pipeline(
        [
            transport.input(),  # Audio from caller
            stt,  # Speech-to-text
            context_aggregator.user(),  # Save user message to context
            llm,  # Generate response
            tts,  # Text-to-speech
            transport.output(),  # Send audio back to caller
            context_aggregator.assistant(),  # Save assistant response to context
        ]
    )

    # ========== 6. Create the Task ==========
    task = PipelineTask(
        pipeline,
        params=PipelineParams(
            enable_metrics=True,
            enable_usage_metrics=True,
        ),
        idle_timeout_secs=runner_args.pipeline_idle_timeout_secs,
    )

    # ========== 7. Event Handlers ==========
    @transport.event_handler("on_client_connected")
    async def on_client_connected(transport, client):
        """Called when a client connects (e.g., Twilio call starts)."""
        logger.info(f"📞 Client connected: {client}")
        # Kick off the conversation with a greeting
        greeting_prompt = os.getenv(
            "GREETING_PROMPT", "Salue l'appelant et présente-toi brièvement."
        )
        messages.append({"role": "system", "content": greeting_prompt})
        await task.queue_frames([LLMRunFrame()])

    @transport.event_handler("on_client_disconnected")
    async def on_client_disconnected(transport, client):
        """Called when client disconnects (call ends)."""
        logger.info(f"📴 Client disconnected: {client}")
        await task.cancel()

    # ========== 8. Run the Pipeline ==========
    runner = PipelineRunner(handle_sigint=runner_args.handle_sigint)
    await runner.run(task)


async def bot(runner_args: RunnerArguments):
    """Main bot entry point compatible with Pipecat Cloud and CLI."""
    transport = await create_transport(runner_args, transport_params)
    await run_bot(transport, runner_args)


if __name__ == "__main__":
    from pipecat.runner.run import main

    # This will start the bot using Pipecat's CLI runner
    # Usage:
    #   python app/main.py --transport twilio --port 8765
    #   python app/main.py --transport daily --room-url <DAILY_ROOM_URL>
    main()
