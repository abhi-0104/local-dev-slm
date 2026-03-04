from fastapi import FastAPI

app = FastAPI(title="Local Enterprise SLM")

@app.get("/health")
def health_check():
    return {"status": "ok", "message": "System is running"}