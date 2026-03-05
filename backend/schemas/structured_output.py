from pydantic import BaseModel, Field

class AICodeResponse(BaseModel):
    """The strict JSON shape we FORCE the AI to return."""
    
    # We use 'Field' to provide descriptions. We will inject these descriptions 
    # directly into the AI's prompt so it knows exactly what we want!
    
    code: str = Field(
        description="Only the raw, executable code. No markdown formatting, no backticks."
    )
    explanation: str = Field(
        description="A brief, professional explanation of how the code works."
    )
    review_notes: str = Field(
        description="Any potential edge cases, security risks, or warnings about this code."
    )

class AIReviewResponse(BaseModel):
    """The strict JSON shape we FORCE the AI to return for code reviews."""
    
    issues_found: int = Field(
        description="The total number of bugs, security risks, or logical flaws found. 0 if the code is perfect."
    )
    review_notes: str = Field(
        description="A detailed bulleted list explaining each issue and how to fix it. If 0 issues, say 'Code looks good!'"
    )