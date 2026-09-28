import argparse
import asyncio
import os
import sys

from dotenv import load_dotenv

from constants import MAIN_MISSING_ENV_EXIT_CODE

REQUIRED_ENV_VARS = ["BOT_TOKEN", "OWNER_CHAT_ID", "TG_API_ID", "TG_API_HASH", "TG_SESSION"]


def check_required_env() -> None:
    missing = [name for name in REQUIRED_ENV_VARS if not os.getenv(name)]
    if missing:
        print("Не заданы обязательные переменные окружения:")
        for name in missing:
            print(f"  - {name}")
        sys.exit(MAIN_MISSING_ENV_EXIT_CODE)


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Запуск сборки и отправки AI-дайджеста")
    parser.add_argument("--dry-run", action="store_true", default=False)
    args = parser.parse_args()

    load_dotenv()
    check_required_env()

    # Импорт после проверки: bot.py создаёт Bot(token) при импорте и без токена падает раньше.
    from scheduler import run_weekly_digest

    asyncio.run(run_weekly_digest(dry_run=args.dry_run))


if __name__ == "__main__":
    main()
