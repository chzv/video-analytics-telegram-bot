from __future__ import annotations

import logging
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseMiddleware):

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        if isinstance(event, Message):
            user_id = event.from_user.id if event.from_user else "unknown"
            text = event.text or ""
            logger.info("Incoming message from %s: %r", user_id, text)

        result = await handler(event, data)

        if isinstance(event, Message):
            logger.info("Handler finished for user %s", event.from_user.id if event.from_user else "unknown")

        return result
