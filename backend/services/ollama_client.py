from ollama import AsyncClient, ResponseError

from config import settings


class TutorUnavailableError(Exception):
    """Raised when the local model can't be reached or isn't installed."""


async def generate_tutor_response(question: str, grade: int = 2) -> str:
    system_prompt = (
        f"You are a friendly math tutor for a Kenyan Grade {grade} student "
        "using the CBE curriculum. Use simple English and real-life examples "
        "like mangoes or shillings. Show your steps, then end with '= <answer>'."
    )

    # Async client so a slow model reply doesn't block other requests.
    client = AsyncClient(host=settings.OLLAMA_BASE_URL)
    try:
        response = await client.chat(
            model=settings.OLLAMA_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question},
            ],
        )
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
