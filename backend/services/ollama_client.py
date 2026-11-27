import asyncio

from ollama import AsyncClient, ResponseError

from config import settings
from services.prompts import load_prompt


class TutorUnavailableError(Exception):
    """Raised when the local model can't be reached or isn't installed."""


class TutorTimeoutError(Exception):
    """Raised when the model takes longer than OLLAMA_TIMEOUT to reply."""


async def generate_tutor_response(question: str, grade: int = 2) -> str:
    # Teachers can edit the wording in backend/prompts/tutor_system.txt.
    system_prompt = load_prompt("tutor_system", grade=grade)

    # Async client so a slow model reply doesn't block other requests.
    client = AsyncClient(host=settings.OLLAMA_BASE_URL)
    try:
        async with asyncio.timeout(settings.OLLAMA_TIMEOUT):
            response = await client.chat(
                model=settings.OLLAMA_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": question},
                ],
            )
    except TimeoutError as e:
        raise TutorTimeoutError(
            f"The tutor took longer than {settings.OLLAMA_TIMEOUT:g} seconds to answer. "
            "Try again, use a smaller model, or raise OLLAMA_TIMEOUT."
        ) from e
    except ConnectionError as e:
        raise TutorUnavailableError(
            f"Cannot reach Ollama at {settings.OLLAMA_BASE_URL}. Is it running? (`ollama serve`)"
        ) from e
    except ResponseError as e:
        if e.status_code == 404:
            raise TutorUnavailableError(
                f"Model '{settings.OLLAMA_MODEL}' is not installed. "
                f"Run `ollama pull {settings.OLLAMA_MODEL}`."
            ) from e
        raise
    finally:
        await client.close()

    content = response.message.content
    return content if content is not None else ""
