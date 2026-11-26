from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.math_verifier import verify
from services.ollama_client import TutorUnavailableError, generate_tutor_response

router = APIRouter(prefix="/api/tutor", tags=["tutor"])


class TutorRequest(BaseModel):
    question: str
    grade: int = 2


class TutorResponse(BaseModel):
    explanation: str
    model_answer: float | None
    correct_answer: float | None
    is_correct: bool | None
    verification_note: str


@router.post(
    "/ask",
    response_model=TutorResponse,
    responses={503: {"description": "The local AI model is not running or not installed"}},
)
async def ask_tutor(req: TutorRequest):
    try:
        explanation = await generate_tutor_response(req.question, req.grade)
    except TutorUnavailableError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    result = verify(req.question, explanation)
    return TutorResponse(
        explanation=explanation,
        model_answer=result["model_answer"],
        correct_answer=result["correct_answer"],
        is_correct=result["is_correct"],
        verification_note=result["reason"],
    )
