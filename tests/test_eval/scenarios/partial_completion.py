"""Сценарий: студент сделал часть работы, часть пропустил."""

from judge.models.pr import PRContext

from .base import EvalScenario, GroundTruth


def partial_completion_scenario() -> EvalScenario:
    return EvalScenario(
        name="partial_completion",
        description="Студент хорошо написал архитектуру, но use-cases отсутствует полностью, "
        "а метрики — без целевых значений. DoD заполнен частично.",
        pr_context=PRContext(
            repo="vstu-sii/test-eval-repo",
            pr_number=4,
            pr_url="https://github.com/vstu-sii/test-eval-repo/pull/4",
            sender="partial-student",
            branch="lab2-ai-engineer-deliverables",
            head_sha="ddd444",
            body="## DoD\n- [x] README обновлён\n- [x] Архитектура описана\n- [ ] Use-cases задокументированы\n- [ ] Метрики определены",
            created_at="2026-03-19T10:00:00Z",
            installation_id=1,
        ),
        files={
            "README.md": "# Project Delta\n\nСервис аналитики поведения пользователей.\n\n## Запуск\n\n```bash\npython main.py\n```",
            "docs/architecture.md": (
                "# Архитектура\n\n"
                "## Компоненты\n\n"
                "1. **Collector Service** (Python/FastAPI) — собирает события через REST API\n"
                "2. **Event Store** (Kafka) — буферизация и доставка событий\n"
                "3. **Analytics Engine** (PySpark) — batch-обработка, расчёт метрик\n"
                "4. **Dashboard** (Grafana) — визуализация метрик\n"
                "5. **PostgreSQL** — хранение агрегатов\n\n"
                "## Решения\n\n"
                "- Kafka вместо RabbitMQ: нужна гарантия порядка событий и replay\n"
                "- PySpark: объём данных >1M events/day, pandas не справится\n"
                "- Grafana: уже используется в компании, не нужно учить новый инструмент"
            ),
            "docs/metrics.md": "# Метрики\n\n- Время обработки события\n- Количество ошибок\n- Доступность сервиса",
        },
        roster_entry={
            "github_username": "partial-student",
            "full_name": "Козлов Козёл",
            "group_id": "ИВТ-1",
            "team_name": "Team Delta",
            "role": "AI Engineer",
            "topic": "Аналитика поведения",
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
            expected_score_range=(12.0, 28.0),
            must_find_issues=["use-cases отсутствует", "метрики без целевых значений"],
            must_not_miss=["architecture", "use-case", "метрик"],
            expected_artifacts_missing=["docs/use-cases.md"],
            min_criteria_covered=5,
        ),
    )
