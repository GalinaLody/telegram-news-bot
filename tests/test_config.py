from datetime import datetime, timezone

import config
from filtering import assign_topic
from models import News


def make_news(title, summary=""):
    return News(
        title=title,
        url="https://example.com/x",
        source="Test",
        published_at=datetime.now(timezone.utc),
        summary_raw=summary,
        topic="Новости AI",
    )


def test_every_source_topic_is_a_key_in_topics_yaml():
    keywords = config.load_topic_keywords()

    for source in config.load_sources():
        for topic in source.get("topics", []):
            assert topic in keywords, f"темы «{topic}» ({source['name']}) нет в topics.yaml"


def test_empty_keywords_only_for_first_topic_of_source():
    keywords = config.load_topic_keywords()

    for source in config.load_sources():
        for position, topic in enumerate(source.get("topics", [])):
            if not keywords[topic]:
                assert position == 0, (
                    f"у темы «{topic}» нет ключей, но она не первая у источника «{source['name']}»: "
                    "она никогда не будет выбрана"
                )


def test_catch_all_topic_is_fallback_and_keywords_still_win():
    keywords = {"Новости AI": [], "AI-агенты": ["агент"]}
    source_topics = ["Новости AI", "AI-агенты"]

    no_match = make_news("Погода в Стамбуле", "Солнечно")
    agent = make_news("Новый агент от OpenAI")

    assert assign_topic(no_match, source_topics, keywords) == "Новости AI"
    assert assign_topic(agent, source_topics, keywords) == "AI-агенты"
