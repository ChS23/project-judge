"""Сценарий: файлы есть, но документы пустые/stub."""

from judge.models.pr import PRContext

from .base import EvalScenario, GroundTruth


def empty_docs_scenario() -> EvalScenario:
    return EvalScenario(
        name="empty_docs",
        description="Студент создал файлы, но содержимое — заглушки. "
        "README пустой, architecture.md содержит только заголовок, use-cases пустой.",
        pr_context=PRContext(
            repo="vstu-sii/test-eval-repo",
            pr_number=2,
            pr_url="https://github.com/vstu-sii/test-eval-repo/pull/2",
            sender="lazy-student",
            branch="lab2-ai-engineer-deliverables",
            head_sha="bbb222",
            body="## DoD\n- [x] README обновлён\n- [ ] Архитектура описана\n- [ ] Use-cases задокументированы\n- [ ] Метрики определены",
            created_at="2026-03-18T10:00:00Z",
            installation_id=1,
        ),
        files={
            "README.md": "# Project\n\nTODO",
            "docs/architecture.md": "# Архитектура\n\nTODO: описать компоненты",
            "docs/use-cases.md": "",
            "docs/metrics.md": "# Метрики\n\nБудут позже.",
        },
        roster_entry={
            "github_username": "lazy-student",
            "full_name": "Петров Пётр",
            "group_id": "ИВТ-1",
            "team_name": "Team Beta",
            "role": "AI Engineer",
            "topic": "Чат-бот",
        },
        rubrics=[
            {
                "lab_id": "2",
                "deliverable_id": "D1",
                "role": "AI Engineer",
                "criterion": "Архитектура: компоненты и связи",
                "max_score": "10",
                "weight": "1",
            },
            {
                "lab_id": "2",
                "deliverable_id": "D1",
                "role": "AI Engineer",
                "criterion": "Архитектура: обоснование решений",
                "max_score": "10",
                "weight": "1",
            },
            {
                "lab_id": "2",
                "deliverable_id": "D2",
                "role": "AI Engineer",
                "criterion": "Use-cases: полнота сценариев",
                "max_score": "10",
                "weight": "1",
            },
            {
                "lab_id": "2",
                "deliverable_id": "D2",
                "role": "AI Engineer",
                "criterion": "Use-cases: конкретность",
                "max_score": "10",
                "weight": "1",
            },
            {
                "lab_id": "2",
                "deliverable_id": "D3",
                "role": "AI Engineer",
                "criterion": "Метрики: измеримость",
                "max_score": "10",
                "weight": "1",
            },
        ],
        deadline="2026-03-20T23:59:00Z",
        spec_html="<h2>Lab 2 — AI Engineer</h2><h3>D1: Архитектура</h3><p>Описание компонентов.</p><p>Файл: docs/architecture.md</p><h3>D2: Use Cases</h3><p>Сценарии использования.</p><p>Файл: docs/use-cases.md</p><h3>D3: Метрики</h3><p>Метрики с целевыми значениями.</p><p>Файл: docs/metrics.md</p><h3>DoD</h3><ul><li>README обновлён</li><li>Архитектура описана</li><li>Use-cases задокументированы</li><li>Метрики определены</li></ul>",
        ground_truth=GroundTruth(
            expected_score_range=(0.0, 15.0),  # из 50 max, почти всё пустое
            must_find_issues=["пустой", "заглушка", "TODO", "не раскрыт"],
            must_not_miss=["architecture", "use-case", "метрик"],
            min_criteria_covered=5,
        ),
    )
