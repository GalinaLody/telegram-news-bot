"""Краткое содержание новости для дайджеста."""

import html
import re

from constants import DIGEST_SUMMARY_MAX_CHARS


def make_summary(text: str, max_chars: int = DIGEST_SUMMARY_MAX_CHARS) -> str:
    """Превратить сырой текст новости в короткое описание без HTML.

    Args:
        text: Сырой текст новости, возможно с HTML-тегами и сущностями.
        max_chars: Максимальная длина результата без учёта многоточия.

    Returns:
        Очищенный текст; если он длиннее лимита, обрезан по границе слова
        с многоточием в конце.
    """
    text = html.unescape(text)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\s+", " ", text).strip()

    if len(text) <= max_chars:
        return text

    truncated = text[:max_chars]
    last_space = truncated.rfind(" ")
    if last_space > 0:
        truncated = truncated[:last_space]

    return truncated.rstrip() + "…"
