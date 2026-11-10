"""Фильтрация и отбор новостей.

Шаги цепочки между сбором и сборкой дайджеста: удаление повторов, фильтр
по дате, проверка «уже отправлено», отбор по темам.
"""

import html
import re
from datetime import datetime, timedelta, timezone
from typing import Optional, Sequence

import storage
from constants import DIGEST_FILTER_RECENT_DAYS, DIGEST_RANK_TARGET_COUNT
from models import News


def _matches_any(text: str, keywords: list[str]) -> bool:
    """Проверить, начинается ли в тексте хотя бы одно слово с одного из ключей."""
    return any(
        re.search(rf"\b{re.escape(keyword)}\w*", text, re.IGNORECASE) for keyword in keywords
    )


def assign_topic(
    news: News, source_topics: list[str], topic_keywords: dict[str, list[str]]
) -> str:
    """Выбрать тему новости из тем её источника по ключевым словам.

    Сначала перебираются темы источника в заданном порядке и ключи ищутся
    в заголовке; если там совпадений нет, тот же перебор идёт по тексту
    новости (HTML-теги из текста вырезаются, иначе, например, `<code>`
    считалось бы совпадением с ключом «code»).

    Args:
        news: Новость, для которой выбирается тема.
        source_topics: Темы источника в порядке из sources.yaml.
        topic_keywords: Ключевые слова тем (topics.yaml).

    Returns:
        Первая тема с совпадением; если совпадений нет — первая тема источника.
    """
    body = re.sub(r"<[^>]+>", " ", html.unescape(news.summary_raw))
    for text in (news.title, body):
        for topic in source_topics:
            if _matches_any(text, topic_keywords.get(topic, [])):
                return topic
    return source_topics[0]


def group_by_topic(
    news_list: list[News], topic_order: Optional[Sequence[str]] = None
) -> dict[str, list[News]]:
    """Сгруппировать новости по темам.

    Args:
        news_list: Новости в произвольном порядке.
        topic_order: Порядок тем (обычно порядок ключей topics.yaml). Темы,
            которых в нём нет, идут в конце в порядке первого появления.

    Returns:
        Словарь «тема -> новости темы» без пустых тем. Новости внутри темы
        сохраняют исходный порядок.
    """
    by_appearance: dict[str, list[News]] = {}
    for news in news_list:
        by_appearance.setdefault(news.topic, []).append(news)

    groups: dict[str, list[News]] = {}
    for topic in topic_order or ():
        if topic in by_appearance:
            groups[topic] = by_appearance.pop(topic)
    groups.update(by_appearance)
    return groups


def filter_recent(news_list: list[News], days: int = DIGEST_FILTER_RECENT_DAYS) -> list[News]:
    """Оставить новости, опубликованные не раньше чем `days` дней назад.

    Args:
        news_list: Собранные новости.
        days: Ширина окна в днях.

    Returns:
        Свежие новости в исходном порядке.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    return [news for news in news_list if news.published_at >= cutoff]


def remove_duplicates(news_list: list[News]) -> list[News]:
    """Убрать повторы URL внутри одного сбора, оставив первую встреченную новость.

    Args:
        news_list: Новости из всех источников в порядке сбора.

    Returns:
        Новости с уникальными URL, порядок сохранён.
    """
    seen_urls: set[str] = set()
    unique_news: list[News] = []
    for news in news_list:
        if news.url not in seen_urls:
            seen_urls.add(news.url)
            unique_news.append(news)
    return unique_news


def dedupe(news_list: list[News]) -> list[News]:
    """Убрать новости, которые уже были отправлены в прошлых выпусках.

    Args:
        news_list: Новости после фильтра по дате.

    Returns:
        Новости, URL которых ещё нет в таблице sent_news.
    """
    return [news for news in news_list if not storage.is_sent(news.url)]


def rank(
    news_list: list[News],
    target_count: int = DIGEST_RANK_TARGET_COUNT,
    topic_order: Optional[Sequence[str]] = None,
) -> list[News]:
    """Отобрать до `target_count` новостей, поровну чередуя темы.

    Внутри темы новости идут от свежих к старым. Темы обходятся по кругу
    в порядке `topic_order`, остальные — после них в порядке первого появления.

    Args:
        news_list: Новости, прошедшие все фильтры.
        target_count: Максимальное число новостей в выпуске.
        topic_order: Порядок тем (см. group_by_topic).

    Returns:
        Отобранные новости в порядке обхода.
    """
    groups = group_by_topic(news_list, topic_order)
    ordered_topics = list(groups)

    for group in groups.values():
        group.sort(key=lambda n: n.published_at, reverse=True)

    indices = {topic: 0 for topic in ordered_topics}
    result = []
    while len(result) < target_count:
        added_any = False
        for topic in ordered_topics:
            if len(result) >= target_count:
                break
            idx = indices[topic]
            if idx < len(groups[topic]):
                result.append(groups[topic][idx])
                indices[topic] += 1
                added_any = True
        if not added_any:
            break

    return result
