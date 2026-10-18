from pathlib import Path

from briefing.clean import html_to_text, truncate

FIXTURES = Path(__file__).parent / "fixtures"


def test_newsletter_keeps_content_and_drops_footer():
    text = html_to_text((FIXTURES / "newsletter.html").read_text())
    assert "$12.4 billion" in text
    assert "24x forward EBITDA" in text
    for junk in ("View this email", "Unsubscribe", "receiving this email", "123 Main Street"):
        assert junk not in text


def test_truncate_marks_cut_text():
    text = "para one\n\n" + "x" * 100
    assert truncate(text, 1000) == text
    cut = truncate(text, 50)
    assert cut.endswith("[Truncated]") and len(cut) < len(text)
