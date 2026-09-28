import html
import re
from collections import defaultdict
from datetime import datetime, timedelta, timezone

import storage
from constants import (
    DIGEST_BLOCK_SEPARATOR_LEN,
    DIGEST_FILTER_RECENT_DAYS,
    DIGEST_RANK_TARGET_COUNT,
    DIGEST_SUMMARY_MAX_CHARS,
    DIGEST_TELEGRAM_MESSAGE_MAX_LEN,
)
from models import News


def filter_recent(news_list: list[News], days: int = DIGEST_FILTER_RECENT_DAYS) -> list[News]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    return [news for news in news_list if news.published_at >= cutoff]


def dedupe(news_list: list[News]) -> list[News]:
    return [news for news in news_list if not storage.is_sent(news.url)]


def rank(news_list: list[News], target_count: int = DIGEST_RANK_TARGET_COUNT) -> list[News]:
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


def make_summary(text: str, max_chars: int = DIGEST_SUMMARY_MAX_CHARS) -> str:
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
            lines.append(news.published_at.astimezone(timezone.utc).strftime("%d.%m.%Y %H:%M UTC"))
        sections.append("\n".join(lines))

    return "\n\n".join(sections)


def split_for_telegram(text: str, max_len: int = DIGEST_TELEGRAM_MESSAGE_MAX_LEN) -> list[str]:
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
