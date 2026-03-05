from fastapi import FastAPI
from backend.auth.routes import router as auth_router
from backend.core.generator import router as ai_router
from backend.core.reviewer import router as review_router
from backend.core.dual_loop import router as loop_router
from backend.memory.routes import router as memory_router

app = FastAPI(title="Local Enterprise SLM")

app.include_router(auth_router)
app.include_router(ai_router)
app.include_router(review_router)
app.include_router(loop_router)
app.include_router(memory_router)

@app.get("/health")
def health_check():
    return {"status": "ok", "message": "System is running"}