import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import ValidationError

from backend.database.db import get_db
from backend.database.models import User, Message
from backend.schemas.requests import ReviewRequest, ReviewResponse
from backend.schemas.structured_output import AIReviewResponse
from backend.core.ollama_client import generate_text
from backend.auth.utils import get_current_user

router = APIRouter(prefix="/ai", tags=["AI Review"])

@router.post("/review", response_model=ReviewResponse)
def review_code(
    request: ReviewRequest, 
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """Acts as a Senior Developer and reviews code for flaws."""
    
    # 1. Save the Human's code submission to the database
    human_msg = Message(
        conversation_id=request.conversation_id, 
        role="user", 
        content=f"Please review this {request.language} code:\n\n{request.code}"
    )
    db.add(human_msg)
    db.commit()

    # 2. Build the Senior Developer Prompt
    sys_prompt = f"""You are a strict, senior {request.language} developer reviewing a junior's code.
    Analyze the code for bugs, inefficiencies, edge cases, and security risks.
    You MUST respond with a valid JSON object containing exactly these two keys:
    - "issues_found": An integer representing the number of flaws found (0 if perfect).
    - "review_notes": A detailed explanation of the issues.
    Do NOT output markdown blocks.
    """

    # 3. The Retry Engine (Same as Generator!)
    max_retries = 3
    final_structured_data = None

    for attempt in range(max_retries):
        ai_response_text = generate_text(
            prompt=f"Review this code:\n{request.code}", 
            model=request.model, 
            system_prompt=sys_prompt, 
            require_json=True
        )

        try:
            parsed_json = json.loads(ai_response_text)
            final_structured_data = AIReviewResponse(**parsed_json)
            break 
            
        except (json.JSONDecodeError, ValidationError) as e:
            if attempt == max_retries - 1:
                raise HTTPException(status_code=500, detail="AI failed JSON structure.")
            sys_prompt += f"\n\nSystem Error on previous attempt: {e}. Fix JSON and try again."

    # 4. Save the AI's review to history
    if final_structured_data is None:
        raise HTTPException(status_code=500, detail="AI failed to generate valid response after retries.")
    ai_msg = Message(
        conversation_id=request.conversation_id, 
        role="assistant", 
        content=final_structured_data.model_dump_json()
    )
    db.add(ai_msg)
    db.commit()

    return ReviewResponse(
        issues_found=final_structured_data.issues_found,
        review_notes=final_structured_data.review_notes,
        model_used=request.model
    )