"""
utils for claude API

way simpler than gemini, no safety filter bs
"""
import os
from typing import Optional
from anthropic import Anthropic


def get_claude_client(api_key: Optional[str] = None) -> Anthropic:
    """get claude client"""
    # handle both None and empty string
    if not api_key:
        api_key = os.getenv("CLAUDE_API_KEY")
    if not api_key:
        raise ValueError("CLAUDE_API_KEY not found in environment variables")
    return Anthropic(api_key=api_key.strip())


def get_claude_model(model_name: Optional[str] = None) -> str:
    """get model name from env or use default"""
    return model_name or os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514")


def call_claude(
    prompt: str,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    max_tokens: int = 4096,
    temperature: float = 0.3
) -> str:
    """
    simple wrapper to call claude

    args:
        prompt - what to send
        api_key - optional api key (reads from env if not provided)
        model - optional model name (reads from env if not provided)
        max_tokens - max tokens in response
        temperature - temperature for generation

    returns:
        response text from claude

    raises:
        ValueError if API key not found or call fails
    """
    client = get_claude_client(api_key)
    model_name = get_claude_model(model)

    try:
        response = client.messages.create(
            model=model_name,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        return response.content[0].text

    except Exception as e:
        raise ValueError(f"Claude API call failed: {e}")
