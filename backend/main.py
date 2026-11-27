from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from routers.learners import router as learners_router
from routers.lesson import router as lesson_router
from routers.placement import router as placement_router
from routers.tutor import router as tutor_router

app = FastAPI(
    title="Kenya Math Tutor API",
    description="Offline math tutor for Kenyan Lower Primary, Grades 1-3 (CBE aligned)",
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

app.include_router(learners_router)
app.include_router(lesson_router)
app.include_router(placement_router)
app.include_router(tutor_router)


@app.get("/")
async def root():
    return {"status": "ok", "message": "math tutor AI is running"}


@app.get("/health")
async def health_check():
    return {"status": "ok"}
