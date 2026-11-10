"""Точка входа: проверяет окружение и запускает сборку и отправку дайджеста."""

import argparse
import asyncio
import sys

import config
from pipeline import run_weekly_digest


def main() -> None:
    """Разобрать аргументы командной строки и запустить недельный дайджест.

    Флаг --dry-run печатает дайджест вместо отправки и ничего не помечает
    отправленным. Если не заданы обязательные переменные окружения,
    завершает программу с ненулевым кодом.
    """
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Запуск сборки и отправки AI-дайджеста")
    parser.add_argument("--dry-run", action="store_true", default=False)
    args = parser.parse_args()

    config.check_required_env()

    asyncio.run(run_weekly_digest(dry_run=args.dry_run))


if __name__ == "__main__":
    main()
