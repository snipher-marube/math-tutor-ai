from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from routers.tutor import router as tutor_router

app = FastAPI(
    title="Kenya Math Tutor API",
    description="Offline AI math tutor for Kenyan Grade 2 (CBE aligned)",
    version="0.1.0",
)

# Allow the Vite frontend to call this API. Origins come from settings.CORS_ORIGINS.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_headers=["*"],
    allow_methods=["*"],
)

app.include_router(tutor_router)


@app.get("/")
async def root():
    return {"status": "ok", "message": "math tutor AI is running"}


@app.get("/health")
async def health_check():
    return {"status": "ok"}
