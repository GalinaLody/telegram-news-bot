import asyncio
import logging
import os
from typing import Union

from aiogram import Bot, Dispatcher, Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = Router()
bot = Bot(token=BOT_TOKEN)


@router.message(CommandStart())
async def handle_start(message: Message) -> None:
    chat_id = message.chat.id
    print(f"chat_id: {chat_id}")
    await message.answer(f"Ваш chat_id: {chat_id}")


async def send_message(chat_id: Union[int, str], text: str) -> None:
    await bot.send_message(chat_id=chat_id, text=text)


async def main() -> None:
    dispatcher = Dispatcher()
    dispatcher.include_router(router)
    await dispatcher.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
