"""code generator using claude"""
from typing import Optional, List
from ..models.specifications import FormalSpecification, VerificationAttempt
from ..utils.prompts import CODE_GENERATOR_PROMPT, REFINEMENT_PROMPT
from ..utils.claude_utils import call_claude
from ..utils.config import LLMConfig


class CodeGenerator:
    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        self.config = LLMConfig.resolve(api_key, model_name)

    def generate(self, spec: FormalSpecification, previous_attempts: Optional[List[VerificationAttempt]] = None) -> str:
        if previous_attempts:
            return self._refine_code(spec, previous_attempts)
        return self._generate_initial(spec)

    def _generate_initial(self, spec: FormalSpecification) -> str:
        params_str = ", ".join([f"{p.name}: {p.type}" for p in spec.parameters])
        preconditions_str = "\n".join([f"    - {pc}" for pc in spec.preconditions]) or "    - None"
        postconditions_str = "\n".join([f"    - {pc}" for pc in spec.postconditions]) or "    - None"
        prompt = CODE_GENERATOR_PROMPT.format(
            function_name=spec.function_name, parameters=params_str, return_type=spec.return_type,
            description=spec.description or "", preconditions=preconditions_str,
            postconditions=postconditions_str, feedback_section="", previous_attempts=""
        )
        code = call_claude(prompt, self.config.api_key, self.config.model_name, temperature=0.3)
        return code.strip().replace("```python", "").replace("```", "").strip()

    def _refine_code(self, spec: FormalSpecification, previous_attempts: List[VerificationAttempt]) -> str:
        last_attempt = previous_attempts[-1]
        errors_str = "\n".join([f"Line {err.line_number}: {err.error_type} - {err.message}" for err in last_attempt.result.errors])
        prompt = REFINEMENT_PROMPT.format(
            python_code=last_attempt.python_code, dafny_code=last_attempt.dafny_code,
            errors=errors_str, feedback=last_attempt.feedback or ""
        )
        code = call_claude(prompt, self.config.api_key, self.config.model_name, temperature=0.4)
        return code.strip().replace("```python", "").replace("```", "").strip()
