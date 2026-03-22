from judge.agent.tools.spec import (
    _html_to_text,
    _parse_deliverables,
    _parse_dod,
    _parse_expected_files,
)

SAMPLE_HTML = """
<html>
<h2>SA/PO</h2>
<h3>D1 — Product Requirements Document (PRD)</h3>
<p>Role: SA/PO</p>
<code>README.md</code>

<h3>D2 — Use-case Narrative</h3>
<p>Role: Fullstack</p>
<code>docs/use-cases.md</code>

<h3>D3 — Stakeholder Map</h3>
<code>docs/stakeholders.md</code>

<h3>D4 — RACI Matrix</h3>
<code>docs/raci.md</code>

<h2>DoD Чеклист</h2>
<ul>
- Определены сегменты пользователей
- Сформулированы боли
- Описаны use-cases
- Файл README.md в репозитории
</ul>

<h2>MLOps</h2>
<h3>D7 — Docker Compose</h3>
<code>docker-compose.dev.yml</code>
</html>
"""


def test_parse_deliverables():
    result = _parse_deliverables(SAMPLE_HTML)
    ids = [d["id"] for d in result]
    assert "D1" in ids
    assert "D2" in ids
    assert "D3" in ids
    assert "D4" in ids


def test_parse_deliverables_role():
    result = _parse_deliverables(SAMPLE_HTML)
    d1 = next(d for d in result if d["id"] == "D1")
    assert d1["role"] == "SA/PO"


def test_parse_expected_files():
    result = _parse_expected_files(SAMPLE_HTML)
    assert "README.md" in result
    assert "docs/use-cases.md" in result
    assert "docs/stakeholders.md" in result
    assert "docs/raci.md" in result


def test_parse_dod():
    result = _parse_dod(SAMPLE_HTML)
    assert len(result) >= 3
    assert any("сегменты" in c.lower() for c in result)


def test_html_to_text():
    result = _html_to_text("<p>Hello <b>world</b></p>")
    assert "Hello" in result
    assert "world" in result
    assert "<" not in result


def test_html_to_text_strips_scripts():
    html = "<script>var x = 1;</script><p>content</p>"
    result = _html_to_text(html)
    assert "var x" not in result
    assert "content" in result
