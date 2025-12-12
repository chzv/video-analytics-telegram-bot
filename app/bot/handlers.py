import logging

from aiogram import Router
from aiogram.types import Message

from app.nlp.llm_client import parse_user_query
from app.services.video_service import execute_analytics_query

logger = logging.getLogger(__name__)

router = Router()


@router.message()
async def handle_any_message(message: Message) -> None:
    text = message.text or ""

    try:
        parsed = parse_user_query(text)
        value = execute_analytics_query(parsed)
        await message.answer(str(value))
    except Exception as e:
        logger.exception("Failed to handle message from user %s: %s", message.from_user.id, text)
        await message.answer("Не удалось обработать запрос, попробуйте переформулировать.")
