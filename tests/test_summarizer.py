from summarizer import make_summary


class TestMakeSummary:
    def test_strips_html_tags(self):
        text = "<p>Hello <b>world</b></p>"

        assert make_summary(text) == "Hello world"

    def test_truncates_at_word_boundary(self):
        text = "one two three four five"

        result = make_summary(text, max_chars=15)

        assert result == "one two three…"
        assert " …" not in result
