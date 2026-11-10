"""Сборка текста дайджеста и нарезка его на сообщения Telegram."""

from datetime import timezone

from constants import DIGEST_BLOCK_SEPARATOR_LEN, DIGEST_TELEGRAM_MESSAGE_MAX_LEN
from filtering import group_by_topic
from models import News
from summarizer import make_summary


def build_digest(news_list: list[News]) -> str:
    """Собрать текст дайджеста: разделы по темам, внутри — блоки новостей.

    Args:
        news_list: Отобранные новости.

    Returns:
        Единый текст с заголовками тем вида «=== Тема ===».
    """
    sections = []
    for topic, topic_news in group_by_topic(news_list).items():
        lines = [f"=== {topic} ==="]
        for news in topic_news:
            lines.append("")
            lines.append(news.title)
            lines.append(make_summary(news.summary_raw))
            lines.append(news.url)
            lines.append(news.published_at.astimezone(timezone.utc).strftime("%d.%m.%Y %H:%M UTC"))
        sections.append("\n".join(lines))

    return "\n\n".join(sections)


def split_for_telegram(text: str, max_len: int = DIGEST_TELEGRAM_MESSAGE_MAX_LEN) -> list[str]:
    """Разрезать текст дайджеста на части не длиннее `max_len`.

    Резать можно только по границам блоков (пустая строка между блоками).

    Args:
        text: Полный текст дайджеста.
        max_len: Максимальная длина одной части.

    Returns:
        Список частей в исходном порядке.
    """
    blocks = text.split("\n\n")
    parts = []
    current_blocks: list[str] = []
    current_len = 0

    for block in blocks:
        added_len = len(block) if not current_blocks else len(block) + DIGEST_BLOCK_SEPARATOR_LEN

        if current_blocks and current_len + added_len > max_len:
            parts.append("\n\n".join(current_blocks))
            current_blocks = [block]
            current_len = len(block)
        else:
            current_blocks.append(block)
            current_len += added_len

    if current_blocks:
        parts.append("\n\n".join(current_blocks))

    return parts
