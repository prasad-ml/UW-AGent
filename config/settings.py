"""
Configuration management for UW-Agent application.
Uses pydantic-settings for environment variable management.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # OpenAI Configuration
    openai_api_key: str
    openai_model: str = "gpt-4o-mini"
    openai_temperature: float = 0.7
    
    # ChromaDB Configuration
    chroma_persist_directory: str = "./chroma_db"
    chroma_collection_name: str = "underwriting_policies"
    
    # Application Configuration
    app_name: str = "UW-Agent"
    app_version: str = "0.1.0"
    debug_mode: bool = False
    log_level: str = "INFO"
    
    # Policy Configuration
    structured_rules_path: str = "./policies/structured_rules.json"
    policies_directory: str = "./policies"
    
    # Agent Configuration
    agent_timeout_seconds: int = 60
    max_retries: int = 3
    
    # Mock API Configuration (for POC)
    mock_api_delay_min: float = 0.5
    mock_api_delay_max: float = 2.0
    mock_api_success_rate: float = 0.8
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    def get_openai_config(self) -> dict:
        """Get OpenAI configuration dictionary."""
        return {
            "api_key": self.openai_api_key,
            "model": self.openai_model,
            "temperature": self.openai_temperature
        }
    
    def get_chroma_config(self) -> dict:
        """Get ChromaDB configuration dictionary."""
        return {
            "persist_directory": self.chroma_persist_directory,
            "collection_name": self.chroma_collection_name
        }


# Global settings instance
settings = Settings()
