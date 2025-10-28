"""
interface to dafny verifier, runs it and parses results
"""
import subprocess
import tempfile
import os
import re
import time
from typing import Optional
from pathlib import Path

from ..models.specifications import VerificationResult, VerificationError


class DafnyVerifier:
    """interface to dafny"""

    def __init__(self, dafny_path: Optional[str] = None):
        """
        init dafny verifier

        args:
            dafny_path - path to dafny executable (if None assumes its in PATH)
        """
        self.dafny_path = dafny_path or "dafny"
        self._check_dafny_installation()

    def _check_dafny_installation(self):
        """check if dafny is installed"""
        try:
            result = subprocess.run(
                [self.dafny_path, "/version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode != 0:
                raise RuntimeError("Dafny is installed but not working correctly")
        except FileNotFoundError:
            raise RuntimeError(
                "Dafny not found. Please install Dafny and ensure it's in your PATH.\n"
                "Download from: https://github.com/dafny-lang/dafny/releases"
            )
        except subprocess.TimeoutExpired:
            raise RuntimeError("Dafny verification timed out during version check")

    def verify(self, dafny_code: str, timeout: int = 30) -> VerificationResult:
        """
        verify dafny code

        args:
            dafny_code - dafny code as a string
            timeout - max time in seconds to wait

        returns:
            VerificationResult with success status and errors
        """
        # create temp file with dafny code
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.dfy',
            delete=False,
            encoding='utf-8'
        ) as f:
            f.write(dafny_code)
            temp_file = f.name

        try:
            start_time = time.time()

            # run dafny verifier
            result = subprocess.run(
                [self.dafny_path, "verify", temp_file],
                capture_output=True,
                text=True,
                timeout=timeout
            )

            execution_time = time.time() - start_time

            # parse output
            success = result.returncode == 0
            errors = self._parse_errors(result.stdout + "\n" + result.stderr, dafny_code)

            return VerificationResult(
                success=success,
                errors=errors,
                dafny_output=result.stdout + "\n" + result.stderr,
                execution_time=execution_time
            )

        except subprocess.TimeoutExpired:
            return VerificationResult(
                success=False,
                errors=[VerificationError(
                    error_type="timeout",
                    message=f"Verification timed out after {timeout} seconds"
                )],
                dafny_output="Timeout",
                execution_time=timeout
            )

        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_file)
            except:
                pass

    def _parse_errors(self, output: str, dafny_code: str) -> list[VerificationError]:
        """
        Parse Dafny error messages from output.

        Args:
            output: Raw output from Dafny verifier.
            dafny_code: The Dafny code that was verified.

        Returns:
            List of VerificationError objects.
        """
        errors = []

        # Dafny error format: filename(line,col): Error: message
        # or: filename(line,col): error message
        error_pattern = r"(.+\.dfy)\((\d+),(\d+)\):\s*(Error|Warning|Info):\s*(.+)"

        for line in output.split('\n'):
            match = re.search(error_pattern, line)
            if match:
                line_num = int(match.group(2))
                col_num = int(match.group(3))
                error_type = match.group(4).lower()
                message = match.group(5).strip()

                # Classify error type more specifically
                classified_type = self._classify_error(message)

                errors.append(VerificationError(
                    line_number=line_num,
                    column_number=col_num,
                    error_type=classified_type,
                    message=message,
                    suggestion=self._generate_suggestion(classified_type, message)
                ))

        # If no structured errors found but verification failed, capture general error
        if not errors and "error" in output.lower():
            errors.append(VerificationError(
                error_type="verification_failure",
                message=output.strip()
            ))

        return errors

    def _classify_error(self, message: str) -> str:
        """Classify error into specific categories."""
        message_lower = message.lower()

        if "invariant" in message_lower:
            if "might not hold" in message_lower:
                return "invariant_violation"
            elif "might not be maintained" in message_lower:
                return "invariant_not_maintained"
            else:
                return "invariant_error"

        elif "postcondition" in message_lower:
            return "postcondition_violation"

        elif "precondition" in message_lower:
            return "precondition_violation"

        elif "assertion" in message_lower:
            return "assertion_failure"

        elif "type" in message_lower:
            return "type_error"

        elif "decreases" in message_lower:
            return "termination_error"

        elif "timeout" in message_lower:
            return "timeout"

        else:
            return "verification_error"

    def _generate_suggestion(self, error_type: str, message: str) -> str:
        """Generate helpful suggestions based on error type."""
        suggestions = {
            "invariant_violation": (
                "The loop invariant doesn't hold at the start of the loop. "
                "Check what's true about your variables before the loop begins."
            ),
            "invariant_not_maintained": (
                "The loop invariant doesn't hold after a loop iteration. "
                "Check how your variables change during the loop body."
            ),
            "postcondition_violation": (
                "The function doesn't guarantee its postcondition. "
                "Check your return statement and ensure all paths satisfy the postcondition."
            ),
            "precondition_violation": (
                "A function call doesn't satisfy the required precondition. "
                "Ensure all arguments meet the function's requirements."
            ),
            "assertion_failure": (
                "An assertion cannot be proven. "
                "Add intermediate steps or strengthen your loop invariants."
            ),
            "type_error": (
                "There's a type mismatch in your code. "
                "Check that all expressions have compatible types."
            ),
            "termination_error": (
                "Cannot prove that the loop or recursion terminates. "
                "Add a decreases clause showing what gets smaller each iteration."
            ),
        }

        return suggestions.get(error_type, "Review the error message and adjust your code or specifications.")

    def get_version(self) -> str:
        """Get Dafny version string."""
        try:
            result = subprocess.run(
                [self.dafny_path, "/version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.stdout.strip()
        except Exception as e:
            return f"Error getting version: {e}"
