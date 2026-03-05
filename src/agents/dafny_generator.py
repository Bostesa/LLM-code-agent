"""Dafny Generator using Claude"""
from typing import Optional
from ..models.specifications import FormalSpecification
from ..utils.claude_utils import call_claude
from ..utils.prompts import DAFNY_GENERATOR_PROMPT
from ..utils.config import LLMConfig


class DafnyCodeGenerator:
    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        self.config = LLMConfig.resolve(api_key, model_name)

    def generate(self, spec: FormalSpecification, python_code: str) -> str:
        prompt = DAFNY_GENERATOR_PROMPT.format(
            function_name=spec.function_name,
            python_code=python_code,
            preconditions=spec.preconditions,
            postconditions=spec.postconditions,
        )
        code = call_claude(prompt, self.config.api_key, self.config.model_name, temperature=0.2, max_tokens=4096)
        return code.strip().replace("```dafny", "").replace("```", "").strip()
