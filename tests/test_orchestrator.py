"""Integration tests for VerificationOrchestrator with mocked components."""
import pytest
from unittest.mock import patch, MagicMock
from src.agents.orchestrator import VerificationOrchestrator
from src.models.specifications import (
    FormalSpecification,
    Parameter,
    VerificationResult,
    VerificationError,
)


@pytest.fixture
def orchestrator():
    """Create orchestrator with mocked Dafny installation check."""
    with patch.dict("os.environ", {"CLAUDE_API_KEY": "test-key"}), \
         patch("src.verifier.dafny_interface.DafnyVerifier._check_dafny_installation"):
        return VerificationOrchestrator(api_key="test-key", max_iterations=3)


class TestGenerateVerifiedCode:
    def test_success_first_try(
        self, orchestrator, sample_spec, successful_verification
    ):
        with patch.object(orchestrator.spec_parser, "parse", return_value=sample_spec), \
             patch.object(orchestrator.code_generator, "generate", return_value="def f(): pass"), \
             patch.object(orchestrator.dafny_generator, "generate", return_value="method F() {}"), \
             patch.object(orchestrator.verifier, "verify", return_value=successful_verification):

            result = orchestrator.generate_verified_code("find max")
            assert result.success is True
            assert result.verified is True
            assert result.total_iterations == 1
            assert len(result.attempts) == 1

    def test_success_after_retry(
        self, orchestrator, sample_spec, failed_verification, successful_verification
    ):
        with patch.object(orchestrator.spec_parser, "parse", return_value=sample_spec), \
             patch.object(orchestrator.code_generator, "generate", return_value="def f(): pass"), \
             patch.object(orchestrator.dafny_generator, "generate", return_value="method F() {}"), \
             patch.object(orchestrator.verifier, "verify", side_effect=[failed_verification, successful_verification]), \
             patch.object(orchestrator.error_analyzer, "analyze", return_value="Fix the invariant"):

            result = orchestrator.generate_verified_code("find max")
            assert result.success is True
            assert result.total_iterations == 2
            assert len(result.attempts) == 2

    def test_max_iterations_exhausted(
        self, orchestrator, sample_spec, failed_verification
    ):
        with patch.object(orchestrator.spec_parser, "parse", return_value=sample_spec), \
             patch.object(orchestrator.code_generator, "generate", return_value="def f(): pass"), \
             patch.object(orchestrator.dafny_generator, "generate", return_value="method F() {}"), \
             patch.object(orchestrator.verifier, "verify", return_value=failed_verification), \
             patch.object(orchestrator.error_analyzer, "analyze", return_value="Fix invariant"):

            result = orchestrator.generate_verified_code("find max")
            assert result.success is False
            assert result.verified is False
            assert result.total_iterations == 3
            assert len(result.attempts) == 3
            assert "Failed to verify" in result.error_message

    def test_fatal_error_in_spec_parsing(self, orchestrator):
        with patch.object(
            orchestrator.spec_parser, "parse", side_effect=ValueError("bad input")
        ):
            result = orchestrator.generate_verified_code("bad input")
            assert result.success is False
            assert "Fatal error" in result.error_message
            assert result.total_iterations == 0

    def test_exception_in_iteration_recorded(self, orchestrator, sample_spec):
        with patch.object(orchestrator.spec_parser, "parse", return_value=sample_spec), \
             patch.object(orchestrator.code_generator, "generate", side_effect=RuntimeError("API down")):

            result = orchestrator.generate_verified_code("find max")
            assert result.success is False
            assert len(result.attempts) > 0
            assert "API down" in result.attempts[0].feedback

    def test_verbose_mode_does_not_crash(
        self, orchestrator, sample_spec, successful_verification
    ):
        with patch.object(orchestrator.spec_parser, "parse", return_value=sample_spec), \
             patch.object(orchestrator.code_generator, "generate", return_value="def f(): pass"), \
             patch.object(orchestrator.dafny_generator, "generate", return_value="method F() {}"), \
             patch.object(orchestrator.verifier, "verify", return_value=successful_verification):

            result = orchestrator.generate_verified_code("find max", verbose=True)
            assert result.success is True


class TestValidateSetup:
    def test_all_ok(self, orchestrator):
        with patch.object(orchestrator.verifier, "get_version", return_value="Dafny 4.0"), \
             patch.object(orchestrator.spec_parser, "parse", return_value=MagicMock()):
            status = orchestrator.validate_setup()
            assert status["dafny"]["ok"] is True
            assert status["claude_api"]["ok"] is True

    def test_dafny_failure(self, orchestrator):
        with patch.object(orchestrator.verifier, "get_version", side_effect=RuntimeError("not found")), \
             patch.object(orchestrator.spec_parser, "parse", return_value=MagicMock()):
            status = orchestrator.validate_setup()
            assert status["dafny"]["ok"] is False
            assert "not found" in status["dafny"]["error"]

    def test_api_failure(self, orchestrator):
        with patch.object(orchestrator.verifier, "get_version", return_value="Dafny 4.0"), \
             patch.object(orchestrator.spec_parser, "parse", side_effect=ValueError("bad key")):
            status = orchestrator.validate_setup()
            assert status["claude_api"]["ok"] is False
