"""
Prompt templates for LLM interactions.
"""

SPECIFICATION_PARSER_PROMPT = """
You are a formal specification expert. Given a natural language description of a function,
extract a structured formal specification.

User Request:
{user_input}

Provide a JSON response with the following structure:
{{
  "function_name": "name_of_function",
  "parameters": [
    {{"name": "param1", "type": "list[int]", "description": "optional description"}}
  ],
  "return_type": "int",
  "preconditions": [
    "array must not be empty",
    "array must be sorted"
  ],
  "postconditions": [
    "if result >= 0, arr[result] == target",
    "if result < 0, target not in arr"
  ],
  "loop_invariants": [
    "loop variable i is within bounds"
  ],
  "description": "Brief description of what the function does",
  "test_cases": [
    {{"input": {{"arr": [1,2,3], "target": 2}}, "output": 1}},
    {{"input": {{"arr": [1,2,3], "target": 5}}, "output": -1}}
  ]
}}

Guidelines:
- Use Python type hints syntax (list[int], Optional[str], etc.)
- Preconditions describe what must be true about inputs
- Postconditions describe what must be true about outputs
- Loop invariants help prove correctness (predict them if loops are needed)
- Include 3-5 test cases covering edge cases
- Be precise and formal in your language
- Keep postconditions concise (one line each, no complex explanations)
- **IMPORTANT**: Test cases must use valid JSON values only - use empty list [] for empty arrays, use actual integers/strings, NEVER use None/null

CRITICAL: Return ONLY valid, complete JSON. Do NOT wrap in markdown code blocks. Do NOT include any text before or after the JSON. Start with {{ and end with }}.
"""

CODE_GENERATOR_PROMPT = """
You are an expert Python programmer who writes clean, verifiable code.

Specification:
Function Name: {function_name}
Parameters: {parameters}
Return Type: {return_type}
Description: {description}

Preconditions:
{preconditions}

Postconditions:
{postconditions}

{feedback_section}

Generate a Python function that:
1. Includes complete type hints
2. Has a docstring with the formal specification
3. Uses pure functional style (no global state, minimal side effects)
4. Is simple and verifiable
5. Follows the specification exactly

{previous_attempts}

Return ONLY the Python code, no markdown formatting or explanations.
"""

REFINEMENT_PROMPT = """
The previous implementation failed verification. Here's the feedback:

Previous Python Code:
{python_code}

Previous Dafny Code:
{dafny_code}

Verification Errors:
{errors}

Specific Feedback:
{feedback}

Generate an improved Python implementation that addresses these issues.
Focus on:
- Fixing logic errors
- Ensuring loop invariants hold
- Making the code more verifiable

Return ONLY the corrected Python code.
"""

ERROR_ANALYSIS_PROMPT = """
You are a formal verification expert analyzing Dafny verification failures.

Dafny Code:
{dafny_code}

Verification Errors:
{errors}

Analyze these errors and provide:
1. What went wrong (in plain English)
2. Which part of the code caused the failure
3. Specific suggestions to fix it
4. If it's a missing invariant, what invariant is needed

Return a structured analysis in JSON format:
{{
  "error_type": "missing_invariant|incorrect_postcondition|logic_error|type_error",
  "location": "line number or code section",
  "explanation": "what went wrong",
  "suggestion": "specific fix to apply"
}}

Return ONLY valid JSON.
"""

DAFNY_INVARIANT_PROMPT = """
You are a Dafny expert specializing in loop invariants.

For this loop in the function:
{loop_code}

Function specification:
Preconditions: {preconditions}
Postconditions: {postconditions}

Current invariants:
{current_invariants}

Verification failed with: {error_message}

Suggest additional loop invariants that would help verification succeed.
Return them as a JSON list of strings:
["invariant 1", "invariant 2", ...]

Guidelines:
- Invariants must hold before loop, after each iteration, and when loop exits
- Link loop variables to specification conditions
- Bound all variables properly
- Use Dafny syntax (|arr| for length, forall/exists for quantifiers)

Return ONLY valid JSON array.
"""
