import pytest
from unittest.mock import patch

from src.models.specifications import (
    FormalSpecification,
    Parameter,
    VerificationResult,
    VerificationError,
    VerificationAttempt,
)


@pytest.fixture
def sample_spec():
    return FormalSpecification(
        function_name="find_max",
        parameters=[Parameter(name="arr", type="list[int]")],
        return_type="int",
        preconditions=["array must not be empty"],
        postconditions=[
            "result is in the array",
            "result >= every element in the array",
        ],
        description="Find the maximum element in a non-empty array",
    )


@pytest.fixture
def successful_verification():
    return VerificationResult(
        success=True,
        errors=[],
        dafny_output="Dafny program verifier finished with 1 verified, 0 errors",
        execution_time=2.5,
    )


@pytest.fixture
def failed_verification():
    return VerificationResult(
        success=False,
        errors=[
            VerificationError(
                line_number=10,
                column_number=5,
                error_type="invariant_violation",
                message="This loop invariant might not hold on entry",
                suggestion="Check initial values",
            )
        ],
        dafny_output="Error at line 10",
        execution_time=1.0,
    )
