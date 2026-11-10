"""Фильтрация и отбор новостей.

Шаги цепочки между сбором и сборкой дайджеста: удаление повторов, фильтр
по дате, проверка «уже отправлено», отбор по темам.
"""

from datetime import datetime, timedelta, timezone

import storage
from constants import DIGEST_FILTER_RECENT_DAYS, DIGEST_RANK_TARGET_COUNT
from models import News


def group_by_topic(news_list: list[News]) -> dict[str, list[News]]:
    """Сгруппировать новости по темам.

    Args:
        news_list: Новости в произвольном порядке.

    Returns:
        Словарь «тема -> новости темы». Темы идут в порядке первого появления,
        новости внутри темы сохраняют исходный порядок.
    """
    groups: dict[str, list[News]] = {}
    for news in news_list:
        groups.setdefault(news.topic, []).append(news)
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


def rank(news_list: list[News], target_count: int = DIGEST_RANK_TARGET_COUNT) -> list[News]:
    """Отобрать до `target_count` новостей, поровну чередуя темы.

    Внутри темы новости идут от свежих к старым. Темы обходятся по кругу
    в порядке первого появления.

    Args:
        news_list: Новости, прошедшие все фильтры.
        target_count: Максимальное число новостей в выпуске.

    Returns:
        Отобранные новости в порядке обхода.
    """
    groups = group_by_topic(news_list)
    topic_order = list(groups)

    for group in groups.values():
        group.sort(key=lambda n: n.published_at, reverse=True)

    indices = {topic: 0 for topic in topic_order}
    result = []
    while len(result) < target_count:
        added_any = False
        for topic in topic_order:
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
