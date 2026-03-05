"""Smoke tests for CLI argument parsing."""
import pytest
from unittest.mock import patch, MagicMock


class TestCLI:
    def test_missing_api_key_exits(self):
        with patch.dict("os.environ", {}, clear=True), \
             patch("sys.argv", ["cli.py", "find max"]), \
             pytest.raises(SystemExit) as exc_info:
            from cli import main
            main()
        assert exc_info.value.code == 1

    def test_check_flag_success(self):
        mock_orchestrator = MagicMock()
        mock_orchestrator.validate_setup.return_value = {
            "dafny": {"ok": True, "version": "4.0"},
            "claude_api": {"ok": True},
        }
        with patch.dict("os.environ", {"CLAUDE_API_KEY": "test-key"}), \
             patch("sys.argv", ["cli.py", "--check", "dummy"]), \
             patch("cli.VerificationOrchestrator", return_value=mock_orchestrator), \
             pytest.raises(SystemExit) as exc_info:
            from cli import main
            main()
        assert exc_info.value.code == 0

    def test_check_flag_failure(self):
        mock_orchestrator = MagicMock()
        mock_orchestrator.validate_setup.return_value = {
            "dafny": {"ok": False, "error": "not installed"},
            "claude_api": {"ok": True},
        }
        with patch.dict("os.environ", {"CLAUDE_API_KEY": "test-key"}), \
             patch("sys.argv", ["cli.py", "--check", "dummy"]), \
             patch("cli.VerificationOrchestrator", return_value=mock_orchestrator), \
             pytest.raises(SystemExit) as exc_info:
            from cli import main
            main()
        assert exc_info.value.code == 1
