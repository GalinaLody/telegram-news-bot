import argparse
import asyncio
import sys

import config


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Запуск сборки и отправки AI-дайджеста")
    parser.add_argument("--dry-run", action="store_true", default=False)
    args = parser.parse_args()

    config.check_required_env()

    # Импорт после проверки: bot.py создаёт Bot(token) при импорте и без токена падает раньше.
    from scheduler import run_weekly_digest

    asyncio.run(run_weekly_digest(dry_run=args.dry_run))


if __name__ == "__main__":
    main()
