"""error analyzer using claude"""
from typing import Optional
from ..models.specifications import VerificationResult
from ..utils.claude_utils import call_claude
from ..utils.prompts import ERROR_ANALYSIS_PROMPT
from ..utils.config import LLMConfig


class ErrorAnalyzer:
    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        self.config = LLMConfig.resolve(api_key, model_name)

    def analyze(self, dafny_code: str, result: VerificationResult) -> str:
        if result.success:
            return "Verification succeeded!"
        errors_str = "\n".join([f"{e.error_type}: {e.message}" for e in result.errors])
        prompt = ERROR_ANALYSIS_PROMPT.format(dafny_code=dafny_code, errors=errors_str)
        return call_claude(prompt, self.config.api_key, self.config.model_name, temperature=0.2, max_tokens=2048)
