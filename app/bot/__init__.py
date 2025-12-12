from aiogram import Dispatcher

from .handlers import router as main_router
from .middleware import LoggingMiddleware


def register_handlers(dp: Dispatcher) -> None:
    dp.message.middleware(LoggingMiddleware())

    dp.include_router(main_router)
