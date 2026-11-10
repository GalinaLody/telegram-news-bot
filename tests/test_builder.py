from datetime import datetime, timedelta, timezone

from builder import EMPTY_DIGEST_TEXT, build_intro, build_parts
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


def make_many(count_per_topic=3, topics=("A", "B", "C")):
    return [
        make_news(f"{topic}{i}", topic=topic, summary="x" * 100)
        for topic in topics
        for i in range(count_per_topic)
    ]


class TestBuildIntro:
    def test_counts_by_topic_in_body_order(self):
        news_list = [
            make_news("b1", topic="Вайбкодинг"),
            make_news("a1", topic="AI-агенты"),
            make_news("b2", topic="Вайбкодинг"),
        ]
        now = datetime(2026, 11, 10, 4, 0, tzinfo=timezone.utc)

        intro = build_intro(news_list, now=now)

        assert intro == "AI-дайджест за 10.11.2026\nНовостей: 3 — Вайбкодинг: 2, AI-агенты: 1"

    def test_date_is_istanbul_date(self):
        news_list = [make_news("a", topic="A")]
        now = datetime(2026, 11, 9, 22, 30, tzinfo=timezone.utc)

        assert build_intro(news_list, now=now).startswith("AI-дайджест за 10.11.2026\n")

    def test_empty_for_no_news(self):
        assert build_intro([]) == ""


class TestBuildParts:
    def test_groups_by_topic_with_headers(self):
        a = make_news("a", topic="A")
        b = make_news("b", topic="B")

        parts = build_parts([a, b])

        assert len(parts) == 1
        text = parts[0].text
        assert "=== A ===" in text
        assert "=== B ===" in text
        assert text.index("=== A ===") < text.index("=== B ===")

    def test_single_part_when_under_limit(self):
        news_list = [make_news(f"n{i}", topic="A") for i in range(3)]

        parts = build_parts(news_list, max_len=4096)

        assert len(parts) == 1
        assert parts[0].news == news_list

    def test_respects_max_len(self):
        news_list = make_many(count_per_topic=15, topics=("A",))

        parts = build_parts(news_list, max_len=500)

        assert len(parts) > 1
        assert all(len(p.text) <= 500 for p in parts)

    def test_each_news_in_exactly_one_part_in_order(self):
        news_list = make_many(count_per_topic=6)

        parts = build_parts(news_list, max_len=500)

        flat = [news for part in parts for news in part.news]
        assert flat == news_list

    def test_news_block_is_not_split_between_parts(self):
        news_list = make_many(count_per_topic=6)

        parts = build_parts(news_list, max_len=500)

        for part in parts:
            for news in part.news:
                assert news.url in part.text
        # каждая новость присутствует в тексте ровно одной части
        for news in news_list:
            assert sum(news.url in part.text for part in parts) == 1

    def test_header_goes_to_start_of_first_part_only(self):
        news_list = make_many(count_per_topic=6)

        parts = build_parts(news_list, header="HEADER", max_len=500)

        assert parts[0].text.startswith("HEADER\n\n")
        assert all("HEADER" not in p.text for p in parts[1:])
        assert all(len(p.text) <= 500 for p in parts)

    def test_topic_heading_never_hangs_at_end_of_part(self):
        news_list = make_many(count_per_topic=3)

        for max_len in range(280, 900, 7):
            parts = build_parts(news_list, max_len=max_len)

            for part in parts:
                last_line = part.text.rstrip().splitlines()[-1]
                assert not last_line.startswith("==="), f"max_len={max_len}"
            assert [n for p in parts for n in p.news] == news_list

    def test_empty_news_gives_single_part_with_empty_news(self):
        parts = build_parts([])

        assert len(parts) == 1
        assert parts[0].text == EMPTY_DIGEST_TEXT
        assert parts[0].news == []

    def test_empty_news_with_header(self):
        parts = build_parts([], header="HEADER")

        assert len(parts) == 1
        assert parts[0].text == f"HEADER\n\n{EMPTY_DIGEST_TEXT}"
        assert parts[0].news == []
