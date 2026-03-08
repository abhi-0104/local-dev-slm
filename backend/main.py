from fastapi import FastAPI
from backend.auth.routes import router as auth_router
from backend.core.generator import router as ai_router
from backend.core.reviewer import router as review_router
from backend.core.dual_loop import router as loop_router
from backend.memory.routes import router as memory_router
from backend.database.db import engine, Base
from backend.database import models
from fastapi.middleware.cors import CORSMiddleware
from backend.config import settings

# Initialize database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Local Enterprise SLM")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(ai_router)
app.include_router(review_router)
app.include_router(loop_router)
app.include_router(memory_router)

@app.get("/health")
def health_check():
    return {"status": "ok", "message": "System is running"}