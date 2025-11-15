"""Configuration for the Realtime Voice Agent using pydantic BaseSettings.

Put secrets in a `.env` file at the project root or provide them via
environment variables. This centralizes keys and defaults for the
pipeline and server.
"""
from pydantic import BaseSettings, Field
from typing import Optional


class Config(BaseSettings):
    # API keys
    MISTRAL_API_KEY: Optional[str] = Field(None, env="MISTRAL_API_KEY")
    MISTRAL_API_URL: Optional[str] = Field(None, env="MISTRAL_API_URL")

    ELEVENLABS_API_KEY: Optional[str] = Field(None, env="ELEVENLABS_API_KEY")
    ELEVENLABS_VOICE_ID_DEFAULT: str = Field("alloy", env="ELEVENLABS_VOICE_ID_DEFAULT")
    ELEVENLABS_API_URL: Optional[str] = Field(None, env="ELEVENLABS_API_URL")

    # Server
    HOST: str = Field("0.0.0.0", env="HOST")
    PORT: int = Field(8000, env="PORT")

    # Behaviour
    SYSTEM_PROMPT: Optional[str] = Field("You are a helpful voice assistant.", env="SYSTEM_PROMPT")
    LOG_LEVEL: str = Field("INFO", env="LOG_LEVEL")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


config = Config()
