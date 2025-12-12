import asyncio
import logging

from aiogram import Bot, Dispatcher

from .config import settings
from .bot import register_handlers


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    bot = Bot(token=settings.telegram_bot_token)
    dp = Dispatcher()

    register_handlers(dp)

    logging.info("Starting Telegram bot polling...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
