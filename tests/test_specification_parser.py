"""Tests for SpecificationParser -- mocks Claude API calls."""
import pytest
from unittest.mock import patch
from src.agents.specification_parser import SpecificationParser


@pytest.fixture
def parser():
    with patch.dict("os.environ", {"CLAUDE_API_KEY": "test-key"}):
        return SpecificationParser(api_key="test-key")


class TestSpecificationParser:
    def test_parse_valid_json(self, parser):
        valid_response = '''{
            "function_name": "find_max",
            "parameters": [{"name": "arr", "type": "list[int]"}],
            "return_type": "int",
            "preconditions": ["array must not be empty"],
            "postconditions": ["result is max element"],
            "description": "Find the maximum"
        }'''

        with patch(
            "src.agents.specification_parser.call_claude",
            return_value=valid_response,
        ):
            spec = parser.parse("Find max in array")
            assert spec.function_name == "find_max"
            assert len(spec.parameters) == 1
            assert spec.parameters[0].name == "arr"
            assert spec.return_type == "int"
            assert len(spec.preconditions) == 1
            assert len(spec.postconditions) == 1

    def test_parse_json_in_markdown_code_block(self, parser):
        response = '```json\n{"function_name": "foo", "parameters": [], "return_type": "int"}\n```'

        with patch(
            "src.agents.specification_parser.call_claude",
            return_value=response,
        ):
            spec = parser.parse("do something")
            assert spec.function_name == "foo"
            assert spec.parameters == []

    def test_parse_json_with_surrounding_text(self, parser):
        response = 'Here is the spec:\n{"function_name": "bar", "parameters": [], "return_type": "bool"}\nDone!'

        with patch(
            "src.agents.specification_parser.call_claude",
            return_value=response,
        ):
            spec = parser.parse("do something")
            assert spec.function_name == "bar"
            assert spec.return_type == "bool"

    def test_parse_no_json_raises(self, parser):
        with patch(
            "src.agents.specification_parser.call_claude",
            return_value="not json at all",
        ):
            with pytest.raises(ValueError, match="Failed to parse"):
                parser.parse("something")

    def test_parse_invalid_json_raises(self, parser):
        with patch(
            "src.agents.specification_parser.call_claude",
            return_value='{"function_name": invalid}',
        ):
            with pytest.raises(ValueError, match="Failed to parse"):
                parser.parse("something")

    def test_parse_missing_required_field_raises(self, parser):
        response = '{"parameters": [], "return_type": "int"}'
        with patch(
            "src.agents.specification_parser.call_claude",
            return_value=response,
        ):
            with pytest.raises(ValueError):
                parser.parse("something")

    def test_parse_optional_fields_default(self, parser):
        response = '{"function_name": "foo", "parameters": [], "return_type": "int"}'
        with patch(
            "src.agents.specification_parser.call_claude",
            return_value=response,
        ):
            spec = parser.parse("something")
            assert spec.preconditions == []
            assert spec.postconditions == []
            assert spec.description == ""

    def test_missing_api_key_raises(self):
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ValueError, match="CLAUDE_API_KEY"):
                SpecificationParser()
