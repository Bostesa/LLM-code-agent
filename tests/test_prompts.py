"""Tests that prompt templates can be formatted without errors."""
from src.utils.prompts import (
    SPECIFICATION_PARSER_PROMPT,
    CODE_GENERATOR_PROMPT,
    REFINEMENT_PROMPT,
    ERROR_ANALYSIS_PROMPT,
    DAFNY_GENERATOR_PROMPT,
)


class TestSpecParserPrompt:
    def test_formats_with_user_input(self):
        result = SPECIFICATION_PARSER_PROMPT.format(user_input="find max in array")
        assert "find max in array" in result

    def test_contains_json_structure(self):
        result = SPECIFICATION_PARSER_PROMPT.format(user_input="test")
        assert "function_name" in result
        assert "parameters" in result


class TestCodeGeneratorPrompt:
    def test_formats_all_fields(self):
        result = CODE_GENERATOR_PROMPT.format(
            function_name="find_max",
            parameters="arr: list[int]",
            return_type="int",
            description="Find max",
            preconditions="- not empty",
            postconditions="- result is max",
            feedback_section="",
            previous_attempts="",
        )
        assert "find_max" in result
        assert "list[int]" in result


class TestRefinementPrompt:
    def test_formats_all_fields(self):
        result = REFINEMENT_PROMPT.format(
            python_code="def f(): pass",
            dafny_code="method F() {}",
            errors="line 10: error",
            feedback="fix the invariant",
        )
        assert "fix the invariant" in result
        assert "def f(): pass" in result


class TestErrorAnalysisPrompt:
    def test_formats_with_code_and_errors(self):
        result = ERROR_ANALYSIS_PROMPT.format(
            dafny_code="method F() {}",
            errors="invariant_violation: might not hold",
        )
        assert "method F() {}" in result
        assert "invariant_violation" in result

    def test_contains_common_patterns(self):
        result = ERROR_ANALYSIS_PROMPT.format(
            dafny_code="code", errors="errors"
        )
        assert "Common Error Patterns" in result


class TestDafnyGeneratorPrompt:
    def test_formats_all_fields(self):
        result = DAFNY_GENERATOR_PROMPT.format(
            function_name="find_max",
            python_code="def find_max(arr): return max(arr)",
            preconditions=["array must not be empty"],
            postconditions=["result is max element"],
        )
        assert "find_max" in result
        assert "def find_max(arr)" in result

    def test_contains_dafny_examples(self):
        result = DAFNY_GENERATOR_PROMPT.format(
            function_name="test",
            python_code="pass",
            preconditions=[],
            postconditions=[],
        )
        assert "FindMax" in result
        assert "invariant" in result
        assert "decreases" in result

    def test_braces_render_correctly(self):
        result = DAFNY_GENERATOR_PROMPT.format(
            function_name="test",
            python_code="pass",
            preconditions=[],
            postconditions=[],
        )
        # Dafny code blocks should have single braces after formatting
        assert "{\n    result := arr[0];" in result
