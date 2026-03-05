from pydantic import BaseModel
from typing import Optional

class GenerateRequest(BaseModel):
    """The shape of data we expect from the frontend when an employee asks for code."""
    prompt: str
    # If the frontend doesn't specify a model, default to our sweet spot 3B model
    model: str = "llama3.2:3b" 
    # What programming language they want
    language: str = "python"
    # An optional conversation ID if they are continuing an old chat
    conversation_id: Optional[int] = None

class GenerateResponse(BaseModel):
    """The shape of data we send back to the frontend after AI generation."""
    code: str
    explanation: str      # <-- NEW
    review_notes: str     # <-- NEW
    model_used: str
    conversation_id: int

class ReviewRequest(BaseModel):
    """Data sent from frontend to ask for a code review."""
    code: str
    model: str = "llama3.2:3b"
    language: str = "python"
    conversation_id: int # We force them to provide the ID to keep the history linked

class ReviewResponse(BaseModel):
    """Data sent back to frontend after AI reviews the code."""
    issues_found: int
    review_notes: str
    model_used: str

class ImproveRequest(BaseModel):
    """Data sent when a human asks the AI to fix specific flaws in existing code."""
    code: str
    feedback: str
    model: str = "llama3.2:3b" # We default back to the Writer model!
    language: str = "python"
    conversation_id: int

class DualLoopRequest(BaseModel):
    """The setup for the autonomous AI-to-AI loop."""
    prompt: str
    writer_model: str = "llama3.2:3b"
    reviewer_model: str = "phi3:mini" # The Senior Dev!
    language: str = "python"
    max_iterations: int = 3 # Hard stop to prevent infinite loops
    conversation_id: Optional[int] = None

class LoopIteration(BaseModel):
    """A record of one single cycle in the argument."""
    iteration_number: int
    code_generated: str
    review_notes: str
    issues_found: int

class DualLoopResponse(BaseModel):
    """The final package handed to the human after the AIs finish arguing."""
    final_code: str
    iterations: list[LoopIteration] # A list of everything that happened
    total_issues_fixed: int
    conversation_id: int