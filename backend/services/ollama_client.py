from ollama import Client

from config import settings


def generate_tutor_response(question: str, grade: int = 2) -> str:
    system_prompt = (
        f"You are a friendly math tutor for a Kenyan Grade {grade} student "
        "using the CBE curriculum. Use simple English and real-life examples "
        "like mangoes or shillings. Show your steps, then end with '= <answer>'."
    )

    client = Client(host=settings.OLLAMA_BASE_URL)
    response = client.chat(
        model=settings.OLLAMA_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question},
        ],
    )

    content = response.message.content
    return content if content is not None else ""
