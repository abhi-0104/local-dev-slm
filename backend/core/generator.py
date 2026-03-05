import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import cast
from pydantic import ValidationError

from backend.database.db import get_db
from backend.database.models import User, Conversation, Message
from backend.schemas.requests import GenerateRequest, GenerateResponse, ImproveRequest
from backend.schemas.structured_output import AICodeResponse
from backend.core.ollama_client import generate_text
from backend.auth.utils import get_current_user

router = APIRouter(prefix="/ai", tags=["AI Generation"])

@router.post("/generate", response_model=GenerateResponse)
def generate_code(
    request: GenerateRequest, 
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """Generates code with autonomous retry logic for strict JSON formatting."""
    
    # 1. Handle Conversation ID
        # 1. Handle Conversation ID
    if not request.conversation_id:
        # Ask the AI to generate a short, smart title for this chat
        title_prompt = f"Summarize this request in exactly 3 to 5 words. Return ONLY the title, nothing else: {request.prompt}"
        smart_title = generate_text(
            prompt=title_prompt, 
            model=request.model, 
            system_prompt="You are a title generator. Return only a short title. No quotes. No punctuation. No explanation.",
            temperature=0.0
        ).strip().strip('"').strip("'")
        
        # If the AI fails or returns something too long, fall back to the prompt
        if not smart_title or len(smart_title) > 60:
            smart_title = request.prompt[:50] + "..."
        
        new_conv = Conversation(
            user_id=cast(int, current_user.id), 
            title=smart_title,
            model=request.model
        )
        db.add(new_conv)
        db.commit()
        db.refresh(new_conv)
        conv_id = cast(int, new_conv.id) 
    else:
        conv_id = request.conversation_id

    # 2. Save the Human's prompt
    human_msg = Message(conversation_id=conv_id, role="user", content=request.prompt)
    db.add(human_msg)
    db.commit()

        # 3. Build the strict System Prompt
    sys_prompt = f"""You are an expert {request.language} developer.
    You MUST respond with a valid JSON object.
    Do NOT wrap the JSON in markdown blocks.
    The JSON must contain EXACTLY these three keys:
    - "code": The raw executable code.
    - "explanation": A brief explanation of the code.
    - "review_notes": Any edge cases or security warnings.
    """

    # --- NEW: MEMORY INJECTION ---
    # We will build the final string we send to the AI
    ai_prompt = ""
    
    if request.conversation_id:
        # If this is an ongoing chat, grab the last 4 messages from the database
        past_messages = db.query(Message)\
            .filter(Message.conversation_id == conv_id)\
            .order_by(Message.created_at.desc())\
            .limit(4)\
            .all()
            
        # We have to reverse them so they read in chronological order (oldest to newest)
        past_messages.reverse()
        
        # Glue the history together so the AI can read it
                # Glue the history together so the AI can read it
        if past_messages:
            ai_prompt += "Here is the conversation history for context:\n\n"
            for msg in past_messages:
                
                # Force them into standard Python strings to satisfy Pylance
                msg_content = str(msg.content)
                msg_role = str(msg.role)
                
                # We skip the user's current prompt because we just saved it to the DB!
                if msg_content != request.prompt: 
                    speaker = "Human" if msg_role == "user" else "AI"
                    ai_prompt += f"{speaker}: {msg_content}\n\n"
                    
            ai_prompt += "Now, please respond to the Human's newest request:\n"
    # Finally, attach the Human's actual new prompt
    ai_prompt += f"Human: {request.prompt}"
    # -----------------------------

    # 4. THE RETRY ENGINE
    max_retries = 3
    final_structured_data = None

    for attempt in range(max_retries):
        # NOTE: We changed `prompt=current_prompt` to `prompt=ai_prompt` below!
        ai_response_text = generate_text(
            prompt=ai_prompt, 
            model=request.model, 
            system_prompt=sys_prompt, 
            require_json=True
        )

    # 4. THE RETRY ENGINE
    max_retries = 3
    current_prompt = request.prompt
    final_structured_data: AICodeResponse | None = None

    for attempt in range(max_retries):
        # We set require_json=True to force Ollama's straightjacket
        ai_response_text = generate_text(
            prompt=current_prompt, 
            model=request.model, 
            system_prompt=sys_prompt, 
            require_json=True
        )

        try:
            # Attempt to parse the AI's string into a Python dictionary
            parsed_json = json.loads(ai_response_text)
            
            # Attempt to push it through the Pydantic Bouncer
            final_structured_data = AICodeResponse(**parsed_json)
            
            # If we get here without crashing, it worked! Exit the loop.
            break 
            
        except (json.JSONDecodeError, ValidationError) as e:
            print(f"--- AI Failed JSON on attempt {attempt + 1}. Retrying... ---")
            if attempt == max_retries - 1:
                # If we failed 3 times, give up and tell the frontend
                raise HTTPException(status_code=500, detail="AI failed to generate valid JSON after 3 attempts.")
            
            # If we failed, append the exact error to the prompt and try again!
            current_prompt += f"\n\nSystem Error: Your previous response failed with this error: {e}. Please fix the JSON and try again."

    # Ensure final_structured_data is not None before proceeding
    if final_structured_data is None:
        raise HTTPException(status_code=500, detail="AI failed to generate valid JSON after 3 attempts.")

    # 5. Save the AI's raw JSON string to the database history
    ai_msg = Message(conversation_id=conv_id, role="assistant", content=final_structured_data.model_dump_json())
    db.add(ai_msg)
    db.commit()

    # 6. Return the beautifully structured data to the frontend
    return GenerateResponse(
        code=final_structured_data.code,
        explanation=final_structured_data.explanation,
        review_notes=final_structured_data.review_notes,
        model_used=request.model,
        conversation_id=conv_id
    )

@router.post("/improve", response_model=GenerateResponse)
def improve_code(
    request: ImproveRequest, 
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """Takes existing code and human feedback, and generates an improved version."""
    
    # 1. Save the Human's feedback to history
    human_msg = Message(
        conversation_id=request.conversation_id, 
        role="user", 
        content=f"Please improve this {request.language} code.\nCode:\n{request.code}\n\nFeedback:\n{request.feedback}"
    )
    db.add(human_msg)
    db.commit()

    # 2. Build the Improvement System Prompt
    sys_prompt = f"""You are an expert {request.language} developer.
    You have been given existing code and specific feedback on how to fix/improve it.
    Apply the feedback and rewrite the code.
    You MUST respond with a valid JSON object containing EXACTLY:
    - "code": The raw, improved executable code.
    - "explanation": A brief explanation of what you changed.
    - "review_notes": Any remaining edge cases.
    Do NOT output markdown blocks.
    """

    # 3. The Prompt we send to the AI
    ai_prompt = f"Original Code:\n{request.code}\n\nFeedback to apply:\n{request.feedback}"

    # 4. The Retry Engine
    max_retries = 3
    final_structured_data = None

    for attempt in range(max_retries):
        ai_response_text = generate_text(
            prompt=ai_prompt, 
            model=request.model, 
            system_prompt=sys_prompt, 
            require_json=True
        )

        try:
            parsed_json = json.loads(ai_response_text)
            final_structured_data = AICodeResponse(**parsed_json)
            break 
            
        except (json.JSONDecodeError, ValidationError) as e:
            if attempt == max_retries - 1:
                raise HTTPException(status_code=500, detail="AI failed JSON structure.")
            sys_prompt += f"\n\nSystem Error on previous attempt: {e}. Fix JSON and try again."

    # Ensure final_structured_data is not None before proceeding
    if final_structured_data is None:
        raise HTTPException(status_code=500, detail="AI failed to generate valid JSON after 3 attempts.")

    # 5. Save the AI's improved code to history
    ai_msg = Message(
        conversation_id=request.conversation_id, 
        role="assistant", 
        content=final_structured_data.model_dump_json()
    )
    db.add(ai_msg)
    db.commit()

    return GenerateResponse(
        code=final_structured_data.code,
        explanation=final_structured_data.explanation,
        review_notes=final_structured_data.review_notes,
        model_used=request.model,
        conversation_id=request.conversation_id
    )