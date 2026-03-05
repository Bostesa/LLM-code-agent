"""Centralized configuration resolution."""
import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class LLMConfig:
    """Configuration for LLM API access."""
    api_key: str
    model_name: str

    @classmethod
    def resolve(cls, api_key: Optional[str] = None, model_name: Optional[str] = None) -> "LLMConfig":
        """Resolve API key and model name from arguments or environment variables."""
        resolved_key = api_key or os.getenv("CLAUDE_API_KEY")
        if not resolved_key:
            raise ValueError(
                "CLAUDE_API_KEY not found. Set it via environment variable or pass it explicitly."
            )
        resolved_model = model_name or os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514")
        return cls(api_key=resolved_key, model_name=resolved_model)
