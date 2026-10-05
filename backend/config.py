import os
from typing import Set
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_ENV: str = os.getenv("APP_ENV", "development")
    APP_NAME: str = "Redfox AI"
    APP_SUBTITLE: str = "Agentic Security Assessment Platform"
    AGENT_VERSION: str = "0.1.0"

    # Strict target isolation: Only the authorized training target is allowed
    LAB_TARGET: str = os.getenv("LAB_TARGET", "http://juice-shop:3000")
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./redfox_ai.db")

    # LLM configuration
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")
    LLM_TIMEOUT_SECONDS: float = float(os.getenv("LLM_TIMEOUT_SECONDS", "30.0"))

    # Tool execution constraints
    TOOL_TIMEOUT_SECONDS: float = float(os.getenv("TOOL_TIMEOUT_SECONDS", "5.0"))
    MAX_RESPONSE_BYTES: int = int(os.getenv("MAX_RESPONSE_BYTES", str(1024 * 512)))  # 512 KB cap

    # Assessment defaults
    ALLOWED_PROFILE: str = "safe_baseline"

    @property
    def allowed_targets(self) -> Set[str]:
        # Normalize and include the configured target
        targets = {self.LAB_TARGET.strip().rstrip("/")}
        # In development/test mode, also allow local port variant if matching host
        if "juice-shop" in self.LAB_TARGET:
            targets.add("http://localhost:3000")
            targets.add("http://127.0.0.1:3000")
        return targets


settings = Settings()
