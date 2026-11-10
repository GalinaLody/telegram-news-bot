"""Разовая утилита: получает строку сессии Telethon для переменной TG_SESSION.

Запускается вручную локально (нужны TG_API_ID и TG_API_HASH в .env);
потребует номер телефона и код подтверждения из Telegram.
"""

import asyncio

from telethon import TelegramClient
from telethon.sessions import StringSession

import config

api_id = int(config.TG_API_ID)
api_hash = config.TG_API_HASH


async def main() -> None:
    """Авторизоваться в Telegram и напечатать строку сессии."""
    async with TelegramClient(StringSession(), api_id, api_hash) as client:
        print(StringSession.save(client.session))


if __name__ == "__main__":
    asyncio.run(main())
