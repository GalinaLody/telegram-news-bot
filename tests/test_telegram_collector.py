from collectors.telegram_collector import strip_markdown


class TestStripMarkdown:
    def test_removes_bold(self):
        assert strip_markdown("**bold text**") == "bold text"

    def test_removes_underline(self):
        assert strip_markdown("__underlined text__") == "underlined text"

    def test_converts_link_to_plain_text(self):
        assert strip_markdown("[click here](https://example.com)") == "click here"

    def test_removes_single_italic_asterisk(self):
        assert strip_markdown("*italic*") == "italic"

    def test_removes_single_italic_underscore(self):
        assert strip_markdown("_italic_") == "italic"

    def test_combined_markdown(self):
        text = "**Bold** and [a link](https://x.com) and _italic_"

        assert strip_markdown(text) == "Bold and a link and italic"
