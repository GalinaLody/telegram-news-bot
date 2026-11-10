from datetime import datetime, timedelta, timezone

from filtering import (
    assign_topic,
    dedupe,
    filter_recent,
    group_by_topic,
    rank,
    remove_duplicates,
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


HABR_AI_TOPICS = ["AI-агенты", "AI-инструменты", "Работа и заработок с AI"]
KEYWORDS = {
    "AI-агенты": ["агент", "agent", "MCP"],
    "AI-инструменты": ["инструмент", "tool", "релиз"],
    "Работа и заработок с AI": ["заработ", "вакан", "code"],
}


class TestAssignTopic:
    def test_keyword_in_title(self):
        news = make_news("u", title="Новый агент от OpenAI", summary="Без ключей")

        assert assign_topic(news, HABR_AI_TOPICS, KEYWORDS) == "AI-агенты"

    def test_no_keywords_gives_first_topic_of_source(self):
        news = make_news("u", title="Погода в Стамбуле", summary="Солнечно")

        assert assign_topic(news, HABR_AI_TOPICS, KEYWORDS) == "AI-агенты"

    def test_keyword_only_in_summary(self):
        news = make_news("u", title="Заголовок без слов", summary="Вышел новый инструмент")

        assert assign_topic(news, HABR_AI_TOPICS, KEYWORDS) == "AI-инструменты"

    def test_title_match_beats_summary_match_of_earlier_topic(self):
        news = make_news("u", title="Как заработать на нейросетях", summary="Говорим про агентов")

        assert assign_topic(news, HABR_AI_TOPICS, KEYWORDS) == "Работа и заработок с AI"

    def test_first_topic_wins_when_several_match(self):
        news = make_news("u", title="Инструмент для агентов", summary="")

        assert assign_topic(news, HABR_AI_TOPICS, KEYWORDS) == "AI-агенты"

    def test_match_is_case_insensitive_and_starts_at_word_boundary(self):
        agent = make_news("u1", title="АГЕНТЫ наступают", summary="")
        inside_word = make_news("u2", title="Субагентство", summary="")

        assert assign_topic(agent, HABR_AI_TOPICS, KEYWORDS) == "AI-агенты"
        # «агент» внутри слова не считается: совпадений нет, берётся первая тема
        assert assign_topic(inside_word, ["AI-инструменты", "AI-агенты"], KEYWORDS) == (
            "AI-инструменты"
        )

    def test_html_tags_in_summary_do_not_match(self):
        news = make_news("u", title="Заголовок", summary="<pre><code>print(1)</code></pre>")

        # ключ «code» есть у третьей темы, но он только в имени тега
        assert assign_topic(news, HABR_AI_TOPICS, KEYWORDS) == "AI-агенты"

    def test_only_topics_of_the_source_are_considered(self):
        news = make_news("u", title="Вакансия мечты", summary="")

        # у «Работа и заработок» есть ключ «вакан», но этой темы нет у источника
        assert assign_topic(news, ["AI-инструменты", "AI-агенты"], KEYWORDS) == "AI-инструменты"


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
    def test_topics_are_visited_in_topic_order(self):
        news_list = [make_news("n1", topic="Новости AI"), make_news("a1", topic="AI-агенты")]

        result = rank(news_list, target_count=10, topic_order=["AI-агенты", "Новости AI"])

        assert [n.url for n in result] == ["a1", "n1"]

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
