import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import cast, TypeVar, Type
from pydantic import ValidationError

from backend.database.db import get_db
from backend.database.models import User, Conversation, Message
from backend.schemas.requests import DualLoopRequest, DualLoopResponse, LoopIteration
from backend.schemas.structured_output import AICodeResponse, AIReviewResponse
from backend.core.ollama_client import generate_text
from backend.auth.utils import get_current_user

router = APIRouter(prefix="/ai", tags=["Multi-Agent Loop"])

# --- THE DRY HELPER FUNCTION ---
T = TypeVar('T')

def _generate_with_retry(prompt: str, model: str, sys_prompt: str, schema_class: Type[T]) -> T:
    """A generic retry engine that works for BOTH the Writer and the Reviewer."""
    max_retries = 3
    current_sys_prompt = sys_prompt
    
    for attempt in range(max_retries):
        raw_text = generate_text(prompt, model, current_sys_prompt, require_json=True)
        try:
            parsed = json.loads(raw_text)
            return schema_class(**parsed) # Magically converts to whichever schema we passed in!
        except (json.JSONDecodeError, ValidationError) as e:
            if attempt == max_retries - 1:
                raise HTTPException(status_code=500, detail=f"Model {model} failed JSON format.")
            current_sys_prompt += f"\n\nSystem Error: {e}. Fix JSON and try again."
    
    raise HTTPException(status_code=500, detail=f"Model {model} failed after {max_retries} retries.")

# --- THE DUAL LOOP ENGINE ---
@router.post("/dual-loop", response_model=DualLoopResponse)
def run_dual_loop(
    request: DualLoopRequest, 
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """Runs an autonomous writer-reviewer loop until the code is perfect or max iterations hit."""
    
    # 1. Setup the Database Conversation
    if not request.conversation_id:
        new_conv = Conversation(
            user_id=cast(int, current_user.id), 
            title=f"Dual-Loop: {request.prompt[:30]}...", 
            model="multi-agent"
        )
        db.add(new_conv)
        db.commit()
        db.refresh(new_conv)
        conv_id = cast(int, new_conv.id) 
    else:
        conv_id = request.conversation_id

    # Save the initial human prompt
    db.add(Message(conversation_id=conv_id, role="user", content=request.prompt))
    db.commit()

    # 2. Set up the Loop Variables
    iterations: list[LoopIteration] = []
    total_issues = 0
    current_code = ""
    feedback_notes = ""

    # 3. START THE FIGHT!
    print(f"\n--- STARTING DUAL-LOOP (Max {request.max_iterations} Iterations) ---")
    
    for i in range(1, request.max_iterations + 1):
        print(f"\n>> Iteration {i}: Loading Writer ({request.writer_model})...")
        
                # --- WRITER PHASE ---
        if i == 1:
            w_sys_prompt = f"""You are an expert {request.language} developer.
            You MUST output ONLY a raw JSON object. NO markdown formatting. NO conversational text. NO backticks.
            Use EXACTLY this format:
            {{
                "code": "your raw code here",
                "explanation": "brief explanation here",
                "review_notes": "none"
            }}"""
            w_prompt = request.prompt
        else:
            w_sys_prompt = f"""You are an expert {request.language} developer fixing code based on a Senior Developer's review.
            You MUST output ONLY a raw JSON object. NO markdown formatting. NO conversational text. NO backticks.
            Use EXACTLY this format:
            {{
                "code": "your fixed code here",
                "explanation": "what you fixed",
                "review_notes": "none"
            }}"""
            w_prompt = f"Original Code:\n{current_code}\n\nReviewer Feedback:\n{feedback_notes}\n\nApply the feedback and return the new code in JSON format."

        writer_resp = _generate_with_retry(w_prompt, request.writer_model, w_sys_prompt, AICodeResponse)
        current_code = writer_resp.code
        
        # --- REVIEWER PHASE ---
        print(f">> Iteration {i}: Loading Reviewer ({request.reviewer_model})...")
        r_sys_prompt = f"""You are a strict Senior {request.language} Developer. Find bugs, logical flaws, or missing edge cases.
        You MUST output ONLY a raw JSON object. NO markdown formatting. NO conversational text. NO backticks.
        Use EXACTLY this format:
        {{
            "issues_found": <integer number of issues, 0 if perfect>,
            "review_notes": "bulleted list of issues and how to fix them. Or 'Code looks good!' if 0 issues."
        }}"""
        r_prompt = f"Review this code:\n{current_code}"
        
        reviewer_resp = _generate_with_retry(r_prompt, request.reviewer_model, r_sys_prompt, AIReviewResponse)
        issues = reviewer_resp.issues_found
        feedback_notes = reviewer_resp.review_notes
        total_issues += issues

        # --- RECORD THE ROUND ---
        iterations.append(LoopIteration(
            iteration_number=i,
            code_generated=current_code,
            review_notes=feedback_notes,
            issues_found=issues
        ))

        # --- THE STOP CONDITION ---
        if issues == 0:
            print(">> SUCCESS! The Senior Reviewer approved the code. Stopping loop.")
            break 
            
    # 4. Save the Final Results to the Database
    final_msg = f"Dual-Loop Finished after {len(iterations)} iterations. Total issues fixed: {total_issues}.\n\nFinal Code:\n{current_code}"
    db.add(Message(conversation_id=conv_id, role="assistant", content=final_msg))
    db.commit()

    # 5. Hand the entire history package back to the Human!
    return DualLoopResponse(
        final_code=current_code,
        iterations=iterations,
        total_issues_fixed=total_issues,
        conversation_id=conv_id
    )