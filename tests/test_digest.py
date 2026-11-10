from datetime import datetime, timedelta, timezone

from digest import (
    build_digest,
    dedupe,
    filter_recent,
    make_summary,
    rank,
    remove_duplicates,
    split_for_telegram,
)
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


class TestFilterRecent:
    def test_keeps_recent_and_drops_old(self):
        recent = make_news("https://example.com/recent", days_ago=1)
        old = make_news("https://example.com/old", days_ago=10)

        result = filter_recent([recent, old], days=7)

        assert result == [recent]


class TestRemoveDuplicates:
    def test_keeps_first_news_with_same_url(self):
        first = make_news("https://example.com/same", title="First")
        second = make_news("https://example.com/same", title="Second")
        other = make_news("https://example.com/other")

        result = remove_duplicates([first, other, second])

        assert result == [first, other]


class TestDedupe:
    def test_removes_already_sent(self, temp_db):
        import storage

        sent = make_news("https://example.com/sent")
        not_sent = make_news("https://example.com/not-sent")
        storage.mark_sent(sent.url)

        result = dedupe([sent, not_sent])

        assert result == [not_sent]


class TestRank:
    def test_round_robin_and_order(self):
        a1 = make_news("a1", topic="A", days_ago=0)
        a2 = make_news("a2", topic="A", days_ago=1)
        b1 = make_news("b1", topic="B", days_ago=0)

        result = rank([a1, a2, b1], target_count=10)

        assert [n.url for n in result] == ["a1", "b1", "a2"]

    def test_does_not_exceed_target_count(self):
        news_list = [make_news(f"n{i}", topic="A", days_ago=i) for i in range(10)]

        result = rank(news_list, target_count=3)

        assert len(result) == 3


class TestMakeSummary:
    def test_strips_html_tags(self):
        text = "<p>Hello <b>world</b></p>"

        assert make_summary(text) == "Hello world"

    def test_truncates_at_word_boundary(self):
        text = "one two three four five"

        result = make_summary(text, max_chars=15)

        assert result == "one two three…"
        assert " …" not in result


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
