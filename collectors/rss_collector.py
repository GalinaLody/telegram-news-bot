import calendar
import logging
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

import feedparser
import yaml

from models import News

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

logger = logging.getLogger(__name__)

SOURCES_PATH = Path(__file__).resolve().parent.parent / "sources.yaml"


def fetch_rss(
    url: str,
    source_name: str,
    topic: str,
    keywords: Optional[List[str]] = None,
) -> list[News]:
    try:
        feed = feedparser.parse(url)
    except Exception as exc:
        logger.error(f"Ошибка получения RSS {source_name} ({url}): {exc}")
        return []

    if feed.bozo and not feed.entries:
        logger.error(f"Ошибка разбора RSS {source_name} ({url}): {feed.bozo_exception}")
        return []

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

        if getattr(entry, "published_parsed", None):
            published_at = datetime.fromtimestamp(
                calendar.timegm(entry.published_parsed), tz=timezone.utc
            )
        else:
            published_at = datetime.now(timezone.utc)

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


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    with open(SOURCES_PATH, encoding="utf-8") as f:
        sources = yaml.safe_load(f)

    for source in sources:
        if source.get("type") != "rss" or not source.get("enabled"):
            continue

        news_items = fetch_rss(
            url=source["url"],
            source_name=source["name"],
            topic=", ".join(source.get("topics", [])),
            keywords=source.get("keywords"),
        )

        first_title = news_items[0].title if news_items else "—"
        print(f"{source['name']}: получено {len(news_items)} новостей, первая: {first_title}")
