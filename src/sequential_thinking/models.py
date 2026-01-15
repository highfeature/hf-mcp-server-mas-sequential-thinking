from pydantic import (
    BaseModel, 
    ConfigDict, 
    Field,
    field_validator, 
    model_validator, 
    ValidationInfo,
)
from typing import Optional, ClassVar

from src.sequential_thinking.settings import settings


class ThoughtData(BaseModel):
    """
    Represents the data structure for a single thought within the sequential
    thinking process. Serves as the input schema for the 'sequentialthinking' tool.
    """
    thought: str = Field(
        ...,
        description="Content of the current thought or step. Should be specific enough to imply the desired action (e.g., 'Analyze X', 'Critique Y', 'Plan Z', 'Research A').",
        min_length=1
    )
    thoughtNumber: int = Field(
        ...,
        description="Sequence number of this thought (starting from 1).",
        ge=1
    )
    totalThoughts: int = Field(
        ...,
        description="Estimated total number of thoughts required for the entire process.",
        ge=1 # Basic positive check; minimum value is enforced by validator.
    )
    nextThoughtNeeded: bool = Field(
        ...,
        description="Indicates if another thought step is expected after this one."
    )
    isRevision: bool = Field(
        False,
        description="Flags if this thought revises a previous one."
    )
    revisesThought: Optional[int] = Field(
        None,
        description="The 'thoughtNumber' being revised, required if isRevision is True.",
        ge=1
    )
    branchFromThought: Optional[int] = Field(
        None,
        description="The 'thoughtNumber' from which this thought initiates a branch.",
        ge=1
    )
    branchId: Optional[str] = Field(
        None,
        description="A unique identifier for the branch, required if branchFromThought is set."
    )
    needsMoreThoughts: bool = Field(
        False,
        description="Flags if more thoughts are needed beyond the current 'totalThoughts' estimate."
    )

    # Pydantic model configuration
    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid",
        frozen=True,  # Immutable; consider mutability if in-tool modification is needed.
        arbitrary_types_allowed=True,
        json_schema_extra={
            "examples": [
                {
                    "thought": "Analyze the core assumptions of the previous step.",
                    "thoughtNumber": 2,
                    "totalThoughts": 5, # Example reflects minimum
                    "nextThoughtNeeded": True,
                    "isRevision": False,
                    "revisesThought": None,
                    "branchFromThought": None,
                    "branchId": None,
                    "needsMoreThoughts": False
                },
                {
                    "thought": "Critique the proposed solution for potential biases.",
                    "thoughtNumber": 4,
                    "totalThoughts": 5, # Example reflects minimum
                    "nextThoughtNeeded": True,
                    "isRevision": False,
                    "revisesThought": None,
                    "branchFromThought": None,
                    "branchId": None,
                    "needsMoreThoughts": False
                }
            ]
        }
    )

    # --- Validators ---
    MIN_TOTAL_THOUGHTS: ClassVar[int] = 5 # Class constant for minimum required total thoughts.

    @field_validator('totalThoughts')
    @classmethod
    def validate_total_thoughts_minimum(cls, v: int) -> int:
        """Ensures 'totalThoughts' meets the defined minimum requirement."""
        if v < cls.MIN_TOTAL_THOUGHTS:
            settings.logger.info(
                f"Input totalThoughts ({v}) is below suggested minimum {cls.MIN_TOTAL_THOUGHTS}. "
                f"Adjusting to {cls.MIN_TOTAL_THOUGHTS}."
            )
            return cls.MIN_TOTAL_THOUGHTS
        return v

    @field_validator('revisesThought')
    @classmethod
    def validate_revises_thought(cls, v: Optional[int], info: ValidationInfo) -> Optional[int]:
        """Validates 'revisesThought' logic."""
        is_revision = info.data.get('isRevision', False)
        if v is not None and not is_revision:
            raise ValueError('revisesThought can only be set when isRevision is True')
        # Ensure the revised thought number is valid and precedes the current thought
        if v is not None and 'thoughtNumber' in info.data and v >= info.data['thoughtNumber']:
            raise ValueError('revisesThought must be less than thoughtNumber')
        return v

    @field_validator('branchId')
    @classmethod
    def validate_branch_id(cls, v: Optional[str], info: ValidationInfo) -> Optional[str]:
        """Validates 'branchId' logic."""
        branch_from_thought = info.data.get('branchFromThought')
        if v is not None and branch_from_thought is None:
            raise ValueError('branchId can only be set when branchFromThought is set')
        return v

    @model_validator(mode='after')
    def validate_thought_numbers(self) -> 'ThoughtData':
        """Performs model-level validation on thought numbering."""
        # Allow thoughtNumber > totalThoughts for dynamic adjustment downstream.
        # revisesThought validation is handled by its field_validator.
        if self.branchFromThought is not None and self.branchFromThought >= self.thoughtNumber:
            raise ValueError('branchFromThought must be less than thoughtNumber')
        # Check for self.thoughtNumber <= self.totalThoughts removed;
        # allows dynamic extension before needsMoreThoughts logic applies.
        # Minimum totalThoughts is handled by its own validator.
        return self

