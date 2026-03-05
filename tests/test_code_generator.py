"""Tests for CodeGenerator with mocked LLM."""
import pytest
from unittest.mock import patch
from src.agents.code_generator import CodeGenerator
from src.models.specifications import VerificationAttempt, VerificationResult, VerificationError


@pytest.fixture
def generator():
    with patch.dict("os.environ", {"CLAUDE_API_KEY": "test-key"}):
        return CodeGenerator(api_key="test-key")


class TestCodeGenerator:
    def test_initial_generation(self, generator, sample_spec):
        response = "```python\ndef find_max(arr):\n    return max(arr)\n```"
        with patch(
            "src.agents.code_generator.call_claude", return_value=response
        ):
            code = generator.generate(sample_spec)
            assert "find_max" in code
            assert "```" not in code  # markdown fences should be stripped

    def test_strips_markdown_fences(self, generator, sample_spec):
        with patch(
            "src.agents.code_generator.call_claude",
            return_value="```python\ncode_here\n```",
        ):
            code = generator.generate(sample_spec)
            assert code == "code_here"

    def test_plain_code_returned_as_is(self, generator, sample_spec):
        with patch(
            "src.agents.code_generator.call_claude",
            return_value="def foo(): pass",
        ):
            code = generator.generate(sample_spec)
            assert code == "def foo(): pass"

    def test_refinement_uses_previous_attempts(
        self, generator, sample_spec, failed_verification
    ):
        attempt = VerificationAttempt(
            attempt_number=1,
            python_code="old code",
            dafny_code="old dafny",
            result=failed_verification,
            feedback="Fix the invariant",
        )
        with patch(
            "src.agents.code_generator.call_claude",
            return_value="def find_max(arr): pass",
        ) as mock_call:
            generator.generate(sample_spec, previous_attempts=[attempt])
            # Verify the refinement prompt was used
            call_args = mock_call.call_args[0][0]
            assert "failed verification" in call_args.lower()

    def test_refinement_includes_errors(
        self, generator, sample_spec, failed_verification
    ):
        attempt = VerificationAttempt(
            attempt_number=1,
            python_code="old code",
            dafny_code="old dafny",
            result=failed_verification,
            feedback="Fix it",
        )
        with patch(
            "src.agents.code_generator.call_claude",
            return_value="def f(): pass",
        ) as mock_call:
            generator.generate(sample_spec, previous_attempts=[attempt])
            call_args = mock_call.call_args[0][0]
            assert "invariant_violation" in call_args
