"""Сборка дайджеста: текст блоков и нарезка на сообщения Telegram."""

from datetime import timezone

from constants import DIGEST_BLOCK_SEPARATOR_LEN, DIGEST_TELEGRAM_MESSAGE_MAX_LEN
from filtering import group_by_topic
from models import DigestPart, News
from summarizer import make_summary

EMPTY_DIGEST_TEXT = "На этой неделе новых новостей не нашлось."


def _format_news(news: News) -> str:
    """Собрать текстовый блок одной новости."""
    return "\n".join(
        [
            news.title,
            make_summary(news.summary_raw),
            news.url,
            news.published_at.astimezone(timezone.utc).strftime("%d.%m.%Y %H:%M UTC"),
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
