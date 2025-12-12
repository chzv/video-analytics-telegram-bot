import json
from typing import Any

import google.generativeai as genai

from app.config import settings
from .prompt_builder import build_prompt
from .query_schema import ParsedQuery


genai.configure(api_key=settings.llm_api_key)

MODEL_NAME = settings.llm_model or "gemini-flash-latest"


def _extract_json_from_response(raw_content: str) -> Any:
    """
    Извлекает JSON-объект из текста, возвращённого моделью.

    Модель по инструкции должна вернуть чистый JSON, но мы
    защищаемся от случайных лишних символов.
    """
    text = raw_content.strip()

    if text.startswith("```"):
        text = text.strip("`")

    first_brace = text.find("{")
    last_brace = text.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        text = text[first_brace : last_brace + 1]

    return json.loads(text)


def parse_user_query(text: str) -> ParsedQuery:
    prompt = build_prompt(text)

    model = genai.GenerativeModel(MODEL_NAME)

    response = model.generate_content(prompt)

    raw = getattr(response, "text", None)
    if not raw:
        if hasattr(response, "candidates") and response.candidates:
            parts = []
            for cand in response.candidates:
                for part in getattr(cand.content, "parts", []):
                    if hasattr(part, "text"):
                        parts.append(part.text)
            raw = "\n".join(parts)
        else:
            raise RuntimeError("Gemini response does not contain text")

    data = _extract_json_from_response(raw)

    return ParsedQuery.model_validate(data)
