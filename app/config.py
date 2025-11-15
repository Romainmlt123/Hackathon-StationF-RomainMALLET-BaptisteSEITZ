"""Configuration centralisée pour l'agent vocal temps réel.

Utilise pydantic BaseSettings pour charger automatiquement depuis .env
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Config(BaseSettings):
    """Configuration avec chargement automatique depuis .env"""

    # ========== API Keys ==========
    MISTRAL_API_KEY: str
    ELEVENLABS_API_KEY: str
    ELEVENLABS_VOICE_ID: str = "alloy"  # ID de voix par défaut

    # ========== Server Configuration ==========
    HOST: str = "0.0.0.0"
    PORT: int = 8765

    # ========== Bot Behavior ==========
    SYSTEM_PROMPT: Optional[str] = None
    GREETING_PROMPT: Optional[str] = None
    LOG_LEVEL: str = "INFO"

    # ========== Twilio (optional) ==========
    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Singleton instance
config = Config()
