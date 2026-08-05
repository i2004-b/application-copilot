"""
Central config for the Application Copilot.

Loads settings from environment variables via .env. Copy .env.example to
.env and fill in your own keys before running anything that hits a real
model API. Nothing in src/ should read os.environ directly -- import
`settings` from here instead, so there's one place to change defaults.
"""
import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    ollama_host: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "llama3.1")
    closed_model: str = os.getenv("CLOSED_MODEL", "claude-haiku-4-5-20251001")
    db_path: str = os.getenv("DB_PATH", "data/copilot.db")
    target_role_types: tuple = field(
        default_factory=lambda: ("SWE", "AI/ML Engineer", "AI/ML Researcher", "TPM/PM", "Other")
    )


settings = Settings()
