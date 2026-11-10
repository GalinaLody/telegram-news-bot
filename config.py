"""Конфигурация проекта: переменные окружения и список источников.

Единственное место, где вызывается load_dotenv(). Остальные модули берут
значения отсюда.
"""

import os
import sys
from pathlib import Path

import yaml
from dotenv import load_dotenv

from constants import MAIN_MISSING_ENV_EXIT_CODE

load_dotenv()

SOURCES_PATH = Path(__file__).resolve().parent / "sources.yaml"
TOPICS_PATH = Path(__file__).resolve().parent / "topics.yaml"

BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_CHAT_ID = os.getenv("OWNER_CHAT_ID")
TG_API_ID = os.getenv("TG_API_ID")
TG_API_HASH = os.getenv("TG_API_HASH")
TG_SESSION = os.getenv("TG_SESSION")

REQUIRED_ENV_VARS = ["BOT_TOKEN", "OWNER_CHAT_ID", "TG_API_ID", "TG_API_HASH", "TG_SESSION"]


def check_required_env() -> None:
    """Проверить, что заданы все обязательные переменные окружения.

    Если чего-то не хватает, печатает список недостающих переменных и
    завершает программу с кодом MAIN_MISSING_ENV_EXIT_CODE.
    """
    missing = [name for name in REQUIRED_ENV_VARS if not os.getenv(name)]
    if missing:
        print("Не заданы обязательные переменные окружения:")
        for name in missing:
            print(f"  - {name}")
        sys.exit(MAIN_MISSING_ENV_EXIT_CODE)


def load_sources() -> list[dict]:
    """Прочитать список источников из sources.yaml.

    Returns:
        Все записи файла, включая отключённые (enabled: false).
    """
    with open(SOURCES_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_topic_keywords() -> dict[str, list[str]]:
    """Прочитать ключевые слова тем из topics.yaml.

    Returns:
        Словарь «тема -> список ключевых слов».
    """
    with open(TOPICS_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)
