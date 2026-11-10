import calendar
import logging
import re
import socket
from datetime import datetime, timezone
from typing import List, Optional

import feedparser

from constants import COLLECTORS_RSS_COLLECTOR_SOCKET_TIMEOUT_SECONDS
from models import News

logger = logging.getLogger(__name__)

# feedparser качает ленты через urllib без таймаута — зависший сервер блокировал бы процесс навечно.
socket.setdefaulttimeout(COLLECTORS_RSS_COLLECTOR_SOCKET_TIMEOUT_SECONDS)


def fetch_rss(
    url: str,
    source_name: str,
    topic: str,
    keywords: Optional[List[str]] = None,
) -> list[News]:
    feed = feedparser.parse(url)

    # feedparser не бросает исключений при сетевых сбоях и таймаутах — только ставит bozo.
    if feed.bozo and not feed.entries:
        raise RuntimeError(f"Не удалось получить RSS {url}: {feed.bozo_exception}")

    keyword_patterns = (
        [re.compile(rf"\b{re.escape(kw)}\w*", re.IGNORECASE) for kw in keywords]
        if keywords
        else None
    )

    news_list = []
    for entry in feed.entries:
        title = entry.get("title", "")

        if keyword_patterns and not any(p.search(title) for p in keyword_patterns):
            continue

        parsed_date = getattr(entry, "published_parsed", None) or getattr(
            entry, "updated_parsed", None
        )
        if not parsed_date:
            logger.warning(f"{source_name}: запись без даты пропущена: {title}")
            continue
        published_at = datetime.fromtimestamp(calendar.timegm(parsed_date), tz=timezone.utc)

        news_list.append(
            News(
                title=title,
                url=entry.get("link", ""),
                source=source_name,
                published_at=published_at,
                summary_raw=entry.get("summary", ""),
                topic=topic,
            )
        )

    return news_list
