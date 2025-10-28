"""
data models for specs and verification results
"""
from typing import List, Optional, Any
from pydantic import BaseModel, Field


class Parameter(BaseModel):
    """function parameter spec"""
    name: str
    type: str
    description: Optional[str] = None


class FormalSpecification(BaseModel):
    """formal spec for a function"""
    function_name: str
    parameters: List[Parameter]
    return_type: str
    preconditions: List[str] = Field(default_factory=list)
    postconditions: List[str] = Field(default_factory=list)
    loop_invariants: List[str] = Field(default_factory=list)
    description: Optional[str] = None
    test_cases: List[dict] = Field(default_factory=list)


class VerificationError(BaseModel):
    """single verification error from dafny"""
    line_number: Optional[int] = None
    column_number: Optional[int] = None
    error_type: str
    message: str
    suggestion: Optional[str] = None


class VerificationResult(BaseModel):
    """result from dafny verification"""
    success: bool
    errors: List[VerificationError] = Field(default_factory=list)
    dafny_output: str
    execution_time: Optional[float] = None


class VerificationAttempt(BaseModel):
    """one verification attempt"""
    attempt_number: int
    python_code: str
    dafny_code: str
    result: Optional[VerificationResult] = None
    feedback: Optional[str] = None


class GenerationResult(BaseModel):
    """final result from code generation and verification"""
    success: bool
    verified: bool
    python_code: Optional[str] = None
    dafny_code: Optional[str] = None
    specification: Optional[FormalSpecification] = None
    attempts: List[VerificationAttempt] = Field(default_factory=list)
    total_iterations: int
    error_message: Optional[str] = None
