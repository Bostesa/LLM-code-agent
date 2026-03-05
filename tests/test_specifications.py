"""Tests for Pydantic data models."""
import pytest
from src.models.specifications import (
    Parameter,
    FormalSpecification,
    VerificationError,
    VerificationResult,
    VerificationAttempt,
    GenerationResult,
)


class TestParameter:
    def test_create_basic(self):
        p = Parameter(name="arr", type="list[int]")
        assert p.name == "arr"
        assert p.type == "list[int]"
        assert p.description is None

    def test_create_with_description(self):
        p = Parameter(name="arr", type="list[int]", description="input array")
        assert p.description == "input array"


class TestFormalSpecification:
    def test_defaults(self):
        spec = FormalSpecification(
            function_name="foo", parameters=[], return_type="int"
        )
        assert spec.preconditions == []
        assert spec.postconditions == []
        assert spec.loop_invariants == []
        assert spec.test_cases == []
        assert spec.description is None

    def test_full_spec(self, sample_spec):
        assert sample_spec.function_name == "find_max"
        assert len(sample_spec.parameters) == 1
        assert sample_spec.parameters[0].name == "arr"
        assert len(sample_spec.preconditions) == 1
        assert len(sample_spec.postconditions) == 2


class TestVerificationError:
    def test_minimal(self):
        err = VerificationError(error_type="type_error", message="bad type")
        assert err.line_number is None
        assert err.column_number is None
        assert err.suggestion is None

    def test_full(self):
        err = VerificationError(
            line_number=5,
            column_number=10,
            error_type="invariant_violation",
            message="invariant might not hold",
            suggestion="fix it",
        )
        assert err.line_number == 5
        assert err.error_type == "invariant_violation"


class TestVerificationResult:
    def test_success(self, successful_verification):
        assert successful_verification.success is True
        assert len(successful_verification.errors) == 0
        assert successful_verification.execution_time == 2.5

    def test_failure(self, failed_verification):
        assert failed_verification.success is False
        assert len(failed_verification.errors) == 1
        assert failed_verification.errors[0].error_type == "invariant_violation"


class TestVerificationAttempt:
    def test_with_none_result(self):
        attempt = VerificationAttempt(
            attempt_number=1, python_code="", dafny_code="", result=None
        )
        assert attempt.result is None
        assert attempt.feedback is None

    def test_with_result_and_feedback(self, failed_verification):
        attempt = VerificationAttempt(
            attempt_number=1,
            python_code="def f(): pass",
            dafny_code="method F() {}",
            result=failed_verification,
            feedback="Fix the loop invariant",
        )
        assert attempt.feedback == "Fix the loop invariant"
        assert attempt.result.success is False


class TestGenerationResult:
    def test_success_result(self, sample_spec):
        result = GenerationResult(
            success=True,
            verified=True,
            python_code="def f(): pass",
            dafny_code="method F() {}",
            specification=sample_spec,
            total_iterations=1,
        )
        assert result.verified is True
        assert result.error_message is None

    def test_failure_result(self):
        result = GenerationResult(
            success=False,
            verified=False,
            total_iterations=5,
            error_message="Failed after 5 iterations",
        )
        assert result.python_code is None
        assert result.dafny_code is None
        assert result.specification is None
        assert result.error_message is not None

    def test_default_attempts(self):
        result = GenerationResult(
            success=False, verified=False, total_iterations=0
        )
        assert result.attempts == []
