import pytest

from urls import normalize_url


def test_utm_variants_and_fragment_give_same_result():
    variants = [
        "https://Habr.com/ru/articles/1/?utm_source=rss&utm_medium=rss",
        "https://habr.com/ru/articles/1/",
        "https://habr.com/ru/articles/1#comments",
    ]

    results = {normalize_url(url) for url in variants}

    assert results == {"https://habr.com/ru/articles/1"}


def test_keeps_other_params_in_original_order():
    url = "https://example.com/page?b=2&utm_campaign=x&a=1&fbclid=abc&gclid=def"

    assert normalize_url(url) == "https://example.com/page?b=2&a=1"


def test_keeps_id_param():
    assert normalize_url("https://example.com/p?id=5&utm_source=rss") == "https://example.com/p?id=5"


@pytest.mark.parametrize(
    "url",
    ["https://example.com/", "https://example.com", "https://t.me/channel/123", ""],
)
def test_root_and_already_clean_urls_are_stable(url):
    assert normalize_url(normalize_url(url)) == normalize_url(url)


def test_root_path_slash_is_kept():
    assert normalize_url("https://Example.com/?utm_source=x") == "https://example.com/"
