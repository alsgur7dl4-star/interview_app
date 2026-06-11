from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.agents_router import router as agents_router
from backend.interview_router import router as interview_router

app = FastAPI(title="AI 이력서 챗봇")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(interview_router)
app.include_router(agents_router)
