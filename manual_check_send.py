import asyncio
import os

from dotenv import load_dotenv

from bot import bot, send_message

load_dotenv()

OWNER_CHAT_ID = os.getenv("OWNER_CHAT_ID")


async def main() -> None:
    try:
        await send_message(OWNER_CHAT_ID, "Тестовое сообщение от бота")
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
