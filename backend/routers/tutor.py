from fastapi import APIRouter
from pydantic import BaseModel

from services.ollama_client import generate_tutor_response

router = APIRouter(prefix="/api/tutor", tags=["tutor"])


class TutorRequest(BaseModel):
    question: str
    grade: int = 2


class TutorResponse(BaseModel):
    explanation: str


@router.post("/ask", response_model=TutorResponse)
async def ask_tutor(req: TutorRequest):
    explanation = generate_tutor_response(req.question, req.grade)
    return TutorResponse(explanation=explanation)
