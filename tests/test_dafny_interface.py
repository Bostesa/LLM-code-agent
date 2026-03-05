"""Tests for DafnyVerifier -- mocks subprocess to avoid requiring Dafny installed."""
import subprocess
import pytest
from unittest.mock import patch, MagicMock
from src.verifier.dafny_interface import DafnyVerifier


@pytest.fixture
def verifier():
    """Create verifier with mocked installation check."""
    with patch.object(DafnyVerifier, "_check_dafny_installation"):
        return DafnyVerifier(dafny_path="/usr/bin/dafny")


class TestVerify:
    def test_verify_success(self, verifier):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = (
            "Dafny program verifier finished with 1 verified, 0 warnings"
        )
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result):
            result = verifier.verify("method Foo() { }")
            assert result.success is True
            assert len(result.errors) == 0
            assert result.execution_time is not None

    def test_verify_failure_with_errors(self, verifier):
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = (
            "test.dfy(10,5): Error: This loop invariant might not hold on entry"
        )
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result):
            result = verifier.verify("method Foo() { while true {} }")
            assert result.success is False
            assert len(result.errors) == 1
            assert result.errors[0].error_type == "invariant_violation"
            assert result.errors[0].line_number == 10
            assert result.errors[0].column_number == 5

    def test_verify_timeout(self, verifier):
        with patch(
            "subprocess.run",
            side_effect=subprocess.TimeoutExpired("dafny", 30),
        ):
            result = verifier.verify("method Slow() { }")
            assert result.success is False
            assert len(result.errors) == 1
            assert result.errors[0].error_type == "timeout"

    def test_verify_multiple_errors(self, verifier):
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = (
            "test.dfy(5,3): Error: postcondition might not hold\n"
            "test.dfy(12,7): Error: assertion might not hold\n"
        )
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result):
            result = verifier.verify("method F() {}")
            assert result.success is False
            assert len(result.errors) == 2

    def test_verify_general_error_fallback(self, verifier):
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = "some error occurred"
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result):
            result = verifier.verify("bad code")
            assert result.success is False
            assert len(result.errors) == 1
            assert result.errors[0].error_type == "verification_failure"


class TestClassifyError:
    def test_invariant_violation(self, verifier):
        assert (
            verifier._classify_error("loop invariant might not hold")
            == "invariant_violation"
        )

    def test_invariant_not_maintained(self, verifier):
        assert (
            verifier._classify_error("invariant might not be maintained")
            == "invariant_not_maintained"
        )

    def test_postcondition_violation(self, verifier):
        assert (
            verifier._classify_error("postcondition might not hold")
            == "postcondition_violation"
        )

    def test_precondition_violation(self, verifier):
        assert (
            verifier._classify_error("precondition might not hold")
            == "precondition_violation"
        )

    def test_assertion_failure(self, verifier):
        assert (
            verifier._classify_error("assertion might not hold")
            == "assertion_failure"
        )

    def test_type_error(self, verifier):
        assert verifier._classify_error("type mismatch") == "type_error"

    def test_termination_error(self, verifier):
        assert (
            verifier._classify_error("decreases not bounded") == "termination_error"
        )

    def test_unknown_error(self, verifier):
        assert (
            verifier._classify_error("something completely different")
            == "verification_error"
        )


class TestGenerateSuggestion:
    def test_known_error_type(self, verifier):
        suggestion = verifier._generate_suggestion("invariant_violation", "")
        assert "doesn't hold at the start" in suggestion

    def test_unknown_error_type(self, verifier):
        suggestion = verifier._generate_suggestion("unknown_type", "")
        assert "Review the error" in suggestion

    def test_postcondition_suggestion(self, verifier):
        suggestion = verifier._generate_suggestion("postcondition_violation", "")
        assert "postcondition" in suggestion


class TestParseErrors:
    def test_no_errors_in_clean_output(self, verifier):
        errors = verifier._parse_errors("everything is fine", "code")
        assert len(errors) == 0

    def test_parses_structured_error(self, verifier):
        output = "test.dfy(15,8): Error: postcondition might not hold"
        errors = verifier._parse_errors(output, "code")
        assert len(errors) == 1
        assert errors[0].line_number == 15
        assert errors[0].column_number == 8

    def test_general_error_fallback(self, verifier):
        output = "some general error message"
        errors = verifier._parse_errors(output, "code")
        assert len(errors) == 1
        assert errors[0].error_type == "verification_failure"


class TestGetVersion:
    def test_get_version_success(self, verifier):
        mock_result = MagicMock()
        mock_result.stdout = "Dafny 4.4.0"

        with patch("subprocess.run", return_value=mock_result):
            version = verifier.get_version()
            assert "Dafny 4.4.0" in version

    def test_get_version_error(self, verifier):
        with patch("subprocess.run", side_effect=Exception("not found")):
            version = verifier.get_version()
            assert "Error" in version


class TestCheckDafnyInstallation:
    def test_not_found_raises(self):
        with patch("subprocess.run", side_effect=FileNotFoundError):
            with pytest.raises(RuntimeError, match="Dafny not found"):
                DafnyVerifier(dafny_path="/nonexistent/dafny")

    def test_bad_returncode_raises(self):
        mock_result = MagicMock()
        mock_result.returncode = 1
        with patch("subprocess.run", return_value=mock_result):
            with pytest.raises(RuntimeError, match="not working correctly"):
                DafnyVerifier(dafny_path="/usr/bin/dafny")

    def test_timeout_raises(self):
        with patch(
            "subprocess.run",
            side_effect=subprocess.TimeoutExpired("dafny", 5),
        ):
            with pytest.raises(RuntimeError, match="timed out"):
                DafnyVerifier(dafny_path="/usr/bin/dafny")
