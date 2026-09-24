import asyncio
import os

from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.sessions import StringSession

load_dotenv()
api_id = int(os.getenv("TG_API_ID"))
api_hash = os.getenv("TG_API_HASH")


async def main() -> None:
    async with TelegramClient(StringSession(), api_id, api_hash) as client:
        print(StringSession.save(client.session))


if __name__ == "__main__":
    asyncio.run(main())
