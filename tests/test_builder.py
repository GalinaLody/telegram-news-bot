from datetime import datetime, timedelta, timezone

from builder import build_digest, split_for_telegram
from models import News


def make_news(url, topic="Тема", days_ago=0, summary="Summary text", title="Title"):
    published_at = datetime.now(timezone.utc) - timedelta(days=days_ago)
    return News(
        title=title,
        url=url,
        source="Test",
        published_at=published_at,
        summary_raw=summary,
        topic=topic,
    )


class TestBuildDigest:
    def test_groups_by_topic_with_headers(self):
        a = make_news("a", topic="A")
        b = make_news("b", topic="B")

        text = build_digest([a, b])

        assert "=== A ===" in text
        assert "=== B ===" in text
        assert text.index("=== A ===") < text.index("=== B ===")


class TestSplitForTelegram:
    def test_respects_limit_and_does_not_split_entries(self):
        news_list = [make_news(f"n{i}", topic="A", summary="x" * 100) for i in range(50)]
        text = build_digest(news_list)

        parts = split_for_telegram(text, max_len=500)

        assert all(len(p) <= 500 for p in parts)
        assert "\n\n".join(parts) == text

    def test_single_part_when_under_limit(self):
        news_list = [make_news(f"n{i}", topic="A") for i in range(3)]
        text = build_digest(news_list)

        parts = split_for_telegram(text, max_len=4096)

        assert len(parts) == 1
        assert parts[0] == text
