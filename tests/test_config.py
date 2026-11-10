import config


def test_topics_yaml_covers_topics_of_multi_topic_sources():
    keywords = config.load_topic_keywords()
    multi_topic_sources = [s for s in config.load_sources() if len(s.get("topics", [])) > 1]

    assert multi_topic_sources
    for source in multi_topic_sources:
        for topic in source["topics"]:
            assert keywords.get(topic), f"нет ключевых слов для темы «{topic}» ({source['name']})"
