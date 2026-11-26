from typing import Annotated

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, StringConstraints

from config import settings
from services.math_verifier import verify
from services.ollama_client import (
    TutorTimeoutError,
    TutorUnavailableError,
    generate_tutor_response,
)

router = APIRouter(prefix="/api/tutor", tags=["tutor"])


# Long enough for a Grade 2 word problem, short enough to keep the model fast.
MAX_QUESTION_LENGTH = 500

Question = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=MAX_QUESTION_LENGTH),
]


class TutorRequest(BaseModel):
    question: Question = Field(
        description="The learner's question. Surrounding spaces are trimmed.",
        examples=["Wanjiru has 5 mangoes and buys 3 more. How many does she have?"],
    )
    grade: int = Field(
        default_factory=lambda: settings.GRADE_LEVEL,
        ge=1,
        le=3,
        description="Grade level (Lower Primary: 1-3). Defaults to GRADE_LEVEL.",
    )


class TutorResponse(BaseModel):
    explanation: str
    model_answer: float | None
    correct_answer: float | None
    is_correct: bool | None
    verification_note: str


@router.post(
    "/ask",
    response_model=TutorResponse,
    responses={
        503: {"description": "The local AI model is not running or not installed"},
        504: {"description": "The model took longer than OLLAMA_TIMEOUT to answer"},
    },
)
async def ask_tutor(req: TutorRequest):
    try:
        explanation = await generate_tutor_response(req.question, req.grade)
    except TutorUnavailableError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    except TutorTimeoutError as e:
        raise HTTPException(status_code=504, detail=str(e)) from e
    result = verify(req.question, explanation)
    return TutorResponse(
        explanation=explanation,
        model_answer=result["model_answer"],
        correct_answer=result["correct_answer"],
        is_correct=result["is_correct"],
        verification_note=result["reason"],
    )
