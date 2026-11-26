from ollama import Client, ResponseError

from config import settings


class TutorUnavailableError(Exception):
    """Raised when the local model can't be reached or isn't installed."""


def generate_tutor_response(question: str, grade: int = 2) -> str:
    system_prompt = (
        f"You are a friendly math tutor for a Kenyan Grade {grade} student "
        "using the CBE curriculum. Use simple English and real-life examples "
        "like mangoes or shillings. Show your steps, then end with '= <answer>'."
    )

    client = Client(host=settings.OLLAMA_BASE_URL)
    try:
        response = client.chat(
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

    content = response.message.content
    return content if content is not None else ""
