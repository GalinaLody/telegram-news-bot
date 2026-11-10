from datetime import datetime, timedelta, timezone

from filtering import dedupe, filter_recent, group_by_topic, rank, remove_duplicates
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


class TestGroupByTopic:
    def test_keeps_first_appearance_order_of_topics(self):
        b1 = make_news("b1", topic="B")
        a1 = make_news("a1", topic="A")
        b2 = make_news("b2", topic="B")

        groups = group_by_topic([b1, a1, b2])

        assert list(groups) == ["B", "A"]
        assert groups["B"] == [b1, b2]
        assert groups["A"] == [a1]

    def test_empty_list_gives_empty_dict(self):
        assert group_by_topic([]) == {}


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
