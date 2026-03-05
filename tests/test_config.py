"""Tests for centralized config resolution."""
import pytest
from unittest.mock import patch
from src.utils.config import LLMConfig


class TestLLMConfig:
    def test_resolve_from_explicit_args(self):
        config = LLMConfig.resolve(api_key="explicit-key", model_name="explicit-model")
        assert config.api_key == "explicit-key"
        assert config.model_name == "explicit-model"

    def test_resolve_from_env(self):
        with patch.dict(
            "os.environ",
            {"CLAUDE_API_KEY": "env-key", "CLAUDE_MODEL": "env-model"},
        ):
            config = LLMConfig.resolve()
            assert config.api_key == "env-key"
            assert config.model_name == "env-model"

    def test_explicit_args_override_env(self):
        with patch.dict(
            "os.environ",
            {"CLAUDE_API_KEY": "env-key", "CLAUDE_MODEL": "env-model"},
        ):
            config = LLMConfig.resolve(api_key="override-key", model_name="override-model")
            assert config.api_key == "override-key"
            assert config.model_name == "override-model"

    def test_resolve_default_model(self):
        with patch.dict("os.environ", {"CLAUDE_API_KEY": "key"}, clear=True):
            config = LLMConfig.resolve()
            assert config.model_name == "claude-sonnet-4-20250514"

    def test_resolve_missing_key_raises(self):
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ValueError, match="CLAUDE_API_KEY"):
                LLMConfig.resolve()

    def test_dataclass_fields(self):
        config = LLMConfig(api_key="key", model_name="model")
        assert config.api_key == "key"
        assert config.model_name == "model"
