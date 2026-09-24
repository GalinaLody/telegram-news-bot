import html
import re
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone

import storage
from models import News

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")


def filter_recent(news_list: list[News], days: int = 7) -> list[News]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    return [news for news in news_list if news.published_at >= cutoff]


def dedupe(news_list: list[News]) -> list[News]:
    return [news for news in news_list if not storage.is_sent(news.url)]


def rank(news_list: list[News], target_count: int = 15) -> list[News]:
    groups: dict[str, list[News]] = defaultdict(list)
    topic_order = []
    for news in news_list:
        if news.topic not in groups:
            topic_order.append(news.topic)
        groups[news.topic].append(news)

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


def make_summary(text: str, max_chars: int = 280) -> str:
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


def build_digest(news_list: list[News]) -> str:
    groups: dict[str, list[News]] = defaultdict(list)
    topic_order = []
    for news in news_list:
        if news.topic not in groups:
            topic_order.append(news.topic)
        groups[news.topic].append(news)

    sections = []
    for topic in topic_order:
        lines = [f"=== {topic} ==="]
        for news in groups[topic]:
            lines.append("")
            lines.append(news.title)
            lines.append(make_summary(news.summary_raw))
            lines.append(news.url)
            lines.append(str(news.published_at))
        sections.append("\n".join(lines))

    return "\n\n".join(sections)


def split_for_telegram(text: str, max_len: int = 4096) -> list[str]:
    blocks = text.split("\n\n")
    parts = []
    current_blocks: list[str] = []
    current_len = 0

    for block in blocks:
        added_len = len(block) if not current_blocks else len(block) + 2

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


if __name__ == "__main__":
    import asyncio

    from collectors.rss_collector import fetch_rss
    from collectors.telegram_collector import fetch_telegram_channel

    habr_news = fetch_rss(
        url="https://habr.com/ru/rss/hub/artificial_intelligence/all/",
        source_name="Habr (хаб AI)",
        topic="AI-агенты",
    )
    print(f"Собрано с Habr: {len(habr_news)}")

    tg_news = asyncio.run(
        fetch_telegram_channel(channel_username="vibecoding_tg", topic="Вайбкодинг", since_days=7)
    )
    print(f"Собрано с @vibecoding_tg: {len(tg_news)}")

    combined_news = habr_news + tg_news
    print(f"Объединено: {len(combined_news)}")

    recent_news = filter_recent(combined_news, days=7)
    print(f"После filter_recent: {len(recent_news)}")

    deduped_news = dedupe(recent_news)
    print(f"После dedupe: {len(deduped_news)}")

    ranked_news = rank(deduped_news, target_count=15)
    print(f"После rank: {len(ranked_news)}\n")

    digest_text = build_digest(ranked_news)
    print(digest_text)

    parts = split_for_telegram(digest_text)
    print(f"\nРазбито на частей: {len(parts)}")
    for i, part in enumerate(parts, start=1):
        print(f"Часть {i}: {len(part)} символов")
