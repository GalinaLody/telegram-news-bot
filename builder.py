"""Сборка дайджеста: текст блоков и нарезка на сообщения Telegram."""

from datetime import datetime, timezone
from typing import Optional

from constants import (
    DIGEST_BLOCK_SEPARATOR_LEN,
    DIGEST_TELEGRAM_MESSAGE_MAX_LEN,
    DIGEST_TIMEZONE,
    DIGEST_TITLE_MAX_CHARS,
)
from filtering import group_by_topic
from models import DigestPart, News
from summarizer import make_summary

EMPTY_DIGEST_TEXT = "На этой неделе новых новостей не нашлось."


def build_intro(news_list: list[News], now: Optional[datetime] = None) -> str:
    """Собрать вступление дайджеста: дата выпуска и число новостей по темам.

    Args:
        news_list: Отобранные новости.
        now: Момент запуска; по умолчанию текущее время. Дата берётся
            по времени Стамбула.

    Returns:
        Две строки вида «AI-дайджест за 10.11.2026» и «Новостей: 3 — Тема: 2, ...»;
        темы идут в том же порядке, что и в теле дайджеста. Для пустого списка
        новостей — пустая строка.
    """
    if not news_list:
        return ""

    now = now or datetime.now(timezone.utc)
    date_text = now.astimezone(DIGEST_TIMEZONE).strftime("%d.%m.%Y")
    counts = ", ".join(
        f"{topic}: {len(topic_news)}" for topic, topic_news in group_by_topic(news_list).items()
    )
    return f"AI-дайджест за {date_text}\nНовостей: {len(news_list)} — {counts}"


def _shorten_title(title: str, max_chars: int = DIGEST_TITLE_MAX_CHARS) -> str:
    """Обрезать слишком длинный заголовок по границе слова и добавить «…».

    Args:
        title: Заголовок новости.
        max_chars: Максимальная длина результата, включая «…».

    Returns:
        Исходный заголовок, если он не длиннее `max_chars`; иначе обрезанный.
        Если в обрезанной части нет пробелов, заголовок режется по длине.
    """
    if len(title) <= max_chars:
        return title
    cut = title[: max_chars - 1]
    if " " in cut and not title[max_chars - 1].isspace():
        cut = cut.rsplit(" ", 1)[0]
    return cut.rstrip(" ,.;:-—") + "…"


def _format_news(news: News) -> str:
    """Собрать текстовый блок одной новости."""
    return "\n".join(
        [
            _shorten_title(news.title),
            make_summary(news.summary_raw),
            news.url,
            news.published_at.astimezone(DIGEST_TIMEZONE).strftime("%d.%m.%Y"),
        ]
    )


def _build_units(news_list: list[News]) -> list[tuple[str, list[News]]]:
    """Разбить дайджест на неделимые единицы «текст + новости в нём».

    Заголовок темы склеивается с первой новостью темы, чтобы он не мог
    остаться в конце части без новостей под ним.
    """
    units: list[tuple[str, list[News]]] = []
    for topic, topic_news in group_by_topic(news_list).items():
        heading = f"=== {topic} ==="
        for index, news in enumerate(topic_news):
            block = _format_news(news)
            if index == 0:
                block = f"{heading}\n\n{block}"
            units.append((block, [news]))
    return units


def build_parts(
    news_list: list[News],
    header: str = "",
    max_len: int = DIGEST_TELEGRAM_MESSAGE_MAX_LEN,
) -> list[DigestPart]:
    """Собрать дайджест и нарезать его на части не длиннее `max_len`.

    Блок новости не разрезается между частями, заголовок темы всегда
    идёт вместе с первой новостью темы, каждая новость попадает ровно в одну
    часть. Единственное исключение из лимита длины: один неделимый блок,
    который сам длиннее `max_len`, уходит отдельной частью целиком.

    Args:
        news_list: Отобранные новости.
        header: Текст в начале первой части (предупреждение, вступление).
        max_len: Максимальная длина одной части.

    Returns:
        Части в порядке отправки. Для пустого списка новостей — одна часть
        с сообщением об отсутствии новостей и пустым `news`.
    """
    units = _build_units(news_list)
    if not units:
        units = [(EMPTY_DIGEST_TEXT, [])]
    if header:
        units.insert(0, (header, []))

    parts: list[DigestPart] = []
    blocks: list[str] = []
    part_news: list[News] = []
    current_len = 0

    for block, block_news in units:
        added_len = len(block) if not blocks else len(block) + DIGEST_BLOCK_SEPARATOR_LEN

        if blocks and current_len + added_len > max_len:
            parts.append(DigestPart(text="\n\n".join(blocks), news=part_news))
            blocks, part_news, current_len = [block], list(block_news), len(block)
        else:
            blocks.append(block)
            part_news.extend(block_news)
            current_len += added_len

    parts.append(DigestPart(text="\n\n".join(blocks), news=part_news))
    return parts
