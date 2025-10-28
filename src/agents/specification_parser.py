"""
spec parser that extracts formal specs from natural language

using claude for way better reliability
"""
import json
import os
from typing import Optional

from ..models.specifications import FormalSpecification, Parameter
from ..utils.prompts import SPECIFICATION_PARSER_PROMPT
from ..utils.claude_utils import call_claude


class SpecificationParser:
    """parses natural language into formal specs using claude"""

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        """
        init the spec parser

        args:
            api_key - claude api key (if None reads from env)
            model_name - claude model name (if None reads from env)
        """
        self.api_key = api_key or os.getenv("CLAUDE_API_KEY")
        if not self.api_key:
            raise ValueError("CLAUDE_API_KEY not found in environment variables")

        self.model_name = model_name or os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514")

    def parse(self, user_input: str) -> FormalSpecification:
        """
        parse natural language into formal spec

        args:
            user_input - what the user wants

        returns:
            FormalSpecification with all the requirements

        raises:
            ValueError if parsing fails
        """
        prompt = SPECIFICATION_PARSER_PROMPT.format(user_input=user_input)

        try:
            # call claude (way simpler than gemini)
            response_text = call_claude(
                prompt,
                api_key=self.api_key,
                model=self.model_name,
                temperature=0.1,  # low temp for consistent parsing
                max_tokens=4096
            )

            # extract JSON from response
            response_text = response_text.strip()

            # remove markdown code blocks if present
            if response_text.startswith('```'):
                # find end of opening code block
                first_newline = response_text.find('\n')
                if first_newline != -1:
                    response_text = response_text[first_newline + 1:]

                # remove closing ```
                if response_text.endswith('```'):
                    response_text = response_text[:-3].strip()

            # try to find JSON in the response
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1

            if json_start == -1 or json_end == 0:
                raise ValueError("No JSON found in response")

            json_text = response_text[json_start:json_end]

            # parse JSON
            try:
                spec_dict = json.loads(json_text)
            except json.JSONDecodeError as e:
                # provide more context about what went wrong
                lines = json_text.split('\n')
                error_line = e.lineno if hasattr(e, 'lineno') else 0
                context_start = max(0, error_line - 2)
                context_end = min(len(lines), error_line + 3)
                context = '\n'.join(f"{i+1}: {lines[i]}" for i in range(context_start, context_end))
                raise ValueError(f"Failed to parse JSON at line {error_line}:\n{context}\n\nError: {e}")

            # convert to pydantic model
            # convert parameters
            parameters = [
                Parameter(name=p["name"], type=p["type"])
                for p in spec_dict.get("parameters", [])
            ]

            return FormalSpecification(
                function_name=spec_dict["function_name"],
                description=spec_dict.get("description", ""),
                parameters=parameters,
                return_type=spec_dict["return_type"],
                preconditions=spec_dict.get("preconditions", []),
                postconditions=spec_dict.get("postconditions", []),
            )

        except Exception as e:
            raise ValueError(f"Failed to parse specification: {e}")
