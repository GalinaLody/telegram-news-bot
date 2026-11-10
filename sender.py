"""Отправка сообщений в Telegram через Bot API.

Последний шаг цепочки: pipeline.py передаёт сюда готовые части дайджеста.
"""

from typing import Union

import requests

import config
from constants import SENDER_TIMEOUT_SECONDS

TELEGRAM_API_URL = "https://api.telegram.org/bot{token}/sendMessage"


class TelegramSendError(Exception):
    """Ошибка отправки сообщения в Telegram.

    В тексте нет URL запроса: он содержит токен бота, а текст ошибки
    попадает в лог и в сообщение об ошибке.
    """


def send_message(chat_id: Union[int, str], text: str) -> None:
    """Отправить текстовое сообщение в чат через Bot API.

    Текст уходит как обычный, без parse_mode.

    Args:
        chat_id: Идентификатор чата получателя.
        text: Текст сообщения.

    Raises:
        TelegramSendError: Telegram вернул ошибку или запрос не удался.
    """
    url = TELEGRAM_API_URL.format(token=config.BOT_TOKEN)

    try:
        response = requests.post(
            url,
            json={"chat_id": chat_id, "text": text},
            timeout=SENDER_TIMEOUT_SECONDS,
        )
    except requests.RequestException as exc:
        # Текст сетевых исключений requests содержит URL с токеном, поэтому берём только тип.
        raise TelegramSendError(f"Запрос к Telegram не удался: {type(exc).__name__}") from None

    try:
        payload = response.json()
    except ValueError:
        payload = {}

    if response.status_code != 200 or payload.get("ok") is not True:
        description = payload.get("description", "нет описания")
        raise TelegramSendError(
            f"Telegram вернул код {response.status_code}: {description}"
        )
