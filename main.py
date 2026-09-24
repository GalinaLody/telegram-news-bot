import argparse
import asyncio

from scheduler import run_weekly_digest


def main() -> None:
    parser = argparse.ArgumentParser(description="Запуск сборки и отправки AI-дайджеста")
    parser.add_argument("--dry-run", action="store_true", default=False)
    args = parser.parse_args()

    asyncio.run(run_weekly_digest(dry_run=args.dry_run))


if __name__ == "__main__":
    main()
