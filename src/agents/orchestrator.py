"""
main orchestrator that coordinates the whole verification process
"""
import logging
from typing import Optional

from .specification_parser import SpecificationParser
from .code_generator import CodeGenerator
from .dafny_generator import DafnyCodeGenerator
from ..verifier.dafny_interface import DafnyVerifier
from ..verifier.error_analyzer import ErrorAnalyzer
from ..models.specifications import (
    GenerationResult,
    VerificationAttempt
)

logger = logging.getLogger(__name__)


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
            verbose - if True enables INFO-level logging

        returns:
            GenerationResult with final code and verification status
        """
        if verbose:
            logging.basicConfig(level=logging.INFO, format="%(message)s")

        spec = None
        attempts = []
        iteration = 0

        try:
            # step 1: parse specification
            logger.info("\n[1/4] Parsing specification...")
            spec = self.spec_parser.parse(user_input)

            logger.info("  Function: %s", spec.function_name)
            logger.info("  Parameters: %d", len(spec.parameters))
            logger.info("  Preconditions: %d", len(spec.preconditions))
            logger.info("  Postconditions: %d", len(spec.postconditions))

            # step 2: generate and verify in a loop
            while iteration < self.max_iterations:
                logger.info("\n[Iteration %d/%d]", iteration + 1, self.max_iterations)

                try:
                    result = None

                    # generate python code
                    logger.info("  [2/4] Generating Python code...")
                    python_code = self.code_generator.generate(spec, attempts)
                    logger.info("  Python code generated")

                    # generate dafny code using LLM
                    logger.info("  [3/4] Generating Dafny code...")
                    dafny_code = self.dafny_generator.generate(spec, python_code)
                    logger.info("  Dafny code generated")

                    # verify with dafny
                    logger.info("  [4/4] Running Dafny verification...")
                    result = self.verifier.verify(dafny_code)

                    if result.success:
                        logger.info("  Verification SUCCEEDED!")
                    else:
                        logger.info("  Verification failed with %d errors", len(result.errors))

                    # Analyze errors if verification failed
                    feedback = None
                    if not result.success:
                        logger.info("  [*] Analyzing errors...")
                        feedback = self.error_analyzer.analyze(dafny_code, result)
                        logger.info("  Feedback: %s...", feedback[:100])

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
                        logger.info("\nSuccessfully verified in %d iteration(s)!", iteration + 1)

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
                    logger.info("  Error in iteration %d: %s", iteration + 1, e)

                    # Record failed attempt
                    attempt = VerificationAttempt(
                        attempt_number=iteration + 1,
                        python_code="",
                        dafny_code="",
                        result=result,
                        feedback=f"Exception during processing: {e}"
                    )
                    attempts.append(attempt)

                    iteration += 1

            # Max iterations reached without success
            logger.info("\nCould not verify after %d iterations", self.max_iterations)

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
                specification=spec,
                attempts=attempts,
                total_iterations=iteration,
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

        # Check Claude API
        try:
            test_spec = self.spec_parser.parse("Write a function that returns 42")
            status['claude_api'] = {'ok': True}
        except Exception as e:
            status['claude_api'] = {'ok': False, 'error': str(e)}

        return status
