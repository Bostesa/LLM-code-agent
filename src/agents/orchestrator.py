"""
main orchestrator that coordinates the whole verification process
"""
from typing import Optional
import time

from .specification_parser import SpecificationParser
from .code_generator import CodeGenerator
from .translator import PythonToDafnyTranslator
from .dafny_generator import DafnyCodeGenerator
from ..verifier.dafny_interface import DafnyVerifier
from ..verifier.error_analyzer import ErrorAnalyzer
from ..models.specifications import (
    FormalSpecification,
    GenerationResult,
    VerificationAttempt
)


class VerificationOrchestrator:
    """orchestrates the whole verification process"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        dafny_path: Optional[str] = None,
        max_iterations: int = 5
    ):
        """
        init the orchestrator

        args:
            api_key - API key for LLM agents
            model_name - model name (if None reads from env)
            dafny_path - path to dafny executable
            max_iterations - max refinement iterations
        """
        self.spec_parser = SpecificationParser(api_key=api_key, model_name=model_name)
        self.code_generator = CodeGenerator(api_key=api_key, model_name=model_name)
        self.translator = PythonToDafnyTranslator()  # keep for fallback
        self.dafny_generator = DafnyCodeGenerator(api_key=api_key, model_name=model_name)
        self.verifier = DafnyVerifier(dafny_path=dafny_path)
        self.error_analyzer = ErrorAnalyzer(api_key=api_key, model_name=model_name)
        self.max_iterations = max_iterations

    def generate_verified_code(
        self,
        user_input: str,
        verbose: bool = False
    ) -> GenerationResult:
        """
        generate and verify code from natural language spec

        args:
            user_input - what the user wants
            verbose - if True prints progress info

        returns:
            GenerationResult with final code and verification status
        """
        try:
            # step 1: parse specification
            if verbose:
                print("\n[1/4] Parsing specification...")
            spec = self.spec_parser.parse(user_input)

            if verbose:
                print(f"  ✓ Function: {spec.function_name}")
                print(f"  ✓ Parameters: {len(spec.parameters)}")
                print(f"  ✓ Preconditions: {len(spec.preconditions)}")
                print(f"  ✓ Postconditions: {len(spec.postconditions)}")

            # step 2: generate and verify in a loop
            attempts = []
            iteration = 0

            while iteration < self.max_iterations:
                if verbose:
                    print(f"\n[Iteration {iteration + 1}/{self.max_iterations}]")

                try:
                    # generate python code
                    if verbose:
                        print("  [2/4] Generating Python code...")
                    python_code = self.code_generator.generate(spec, attempts)

                    if verbose:
                        print("  ✓ Python code generated")

                    # generate dafny code using LLM
                    if verbose:
                        print("  [3/4] Generating Dafny code...")
                    dafny_code = self.dafny_generator.generate(spec, python_code)

                    if verbose:
                        print("  ✓ Dafny code generated")

                    # verify with dafny
                    if verbose:
                        print("  [4/4] Running Dafny verification...")
                    result = self.verifier.verify(dafny_code)

                    if verbose:
                        if result.success:
                            print("  ✓ Verification SUCCEEDED!")
                        else:
                            print(f"  ✗ Verification failed with {len(result.errors)} errors")

                    # Analyze errors if verification failed
                    feedback = None
                    if not result.success:
                        if verbose:
                            print("  [*] Analyzing errors...")
                        feedback = self.error_analyzer.analyze(dafny_code, result)

                        if verbose:
                            print(f"  Feedback: {feedback[:100]}...")

                    # Record attempt
                    attempt = VerificationAttempt(
                        attempt_number=iteration + 1,
                        python_code=python_code,
                        dafny_code=dafny_code,
                        result=result,
                        feedback=feedback
                    )
                    attempts.append(attempt)

                    # Check if successful
                    if result.success:
                        if verbose:
                            print(f"\n✓ Successfully verified in {iteration + 1} iteration(s)!")

                        return GenerationResult(
                            success=True,
                            verified=True,
                            python_code=python_code,
                            dafny_code=dafny_code,
                            specification=spec,
                            attempts=attempts,
                            total_iterations=iteration + 1
                        )

                    iteration += 1

                except Exception as e:
                    if verbose:
                        print(f"  ✗ Error in iteration {iteration + 1}: {e}")

                    # Record failed attempt
                    attempt = VerificationAttempt(
                        attempt_number=iteration + 1,
                        python_code="",
                        dafny_code="",
                        result=result if 'result' in locals() else None,
                        feedback=f"Exception during processing: {e}"
                    )
                    attempts.append(attempt)

                    iteration += 1

            # Max iterations reached without success
            if verbose:
                print(f"\n✗ Could not verify after {self.max_iterations} iterations")

            return GenerationResult(
                success=False,
                verified=False,
                python_code=attempts[-1].python_code if attempts else None,
                dafny_code=attempts[-1].dafny_code if attempts else None,
                specification=spec,
                attempts=attempts,
                total_iterations=self.max_iterations,
                error_message=f"Failed to verify after {self.max_iterations} iterations"
            )

        except Exception as e:
            # Fatal error during process
            return GenerationResult(
                success=False,
                verified=False,
                specification=spec if 'spec' in locals() else None,
                attempts=attempts if 'attempts' in locals() else [],
                total_iterations=iteration if 'iteration' in locals() else 0,
                error_message=f"Fatal error: {e}"
            )

    def validate_setup(self) -> dict:
        """
        Validate that all components are properly set up.

        Returns:
            Dict with status of each component.
        """
        status = {}

        # Check Dafny
        try:
            version = self.verifier.get_version()
            status['dafny'] = {'ok': True, 'version': version}
        except Exception as e:
            status['dafny'] = {'ok': False, 'error': str(e)}

        # Check Gemini API
        try:
            test_spec = self.spec_parser.parse("Write a function that returns 42")
            status['gemini_api'] = {'ok': True}
        except Exception as e:
            status['gemini_api'] = {'ok': False, 'error': str(e)}

        return status
