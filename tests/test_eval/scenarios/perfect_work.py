"""Сценарий: студент сделал всё идеально."""

from judge.models.pr import PRContext

from .base import EvalScenario, GroundTruth


def perfect_work_scenario() -> EvalScenario:
    return EvalScenario(
        name="perfect_work",
        description="Студент сдал Lab 2 как AI Engineer. Все артефакты на месте, "
        "документы содержательные и конкретные, DoD полностью заполнен.",
        pr_context=PRContext(
            repo="vstu-sii/test-eval-repo",
            pr_number=1,
            pr_url="https://github.com/vstu-sii/test-eval-repo/pull/1",
            sender="perfect-student",
            branch="lab2-ai-engineer-deliverables",
            head_sha="aaa111",
            body="## DoD\n- [x] README обновлён\n- [x] Архитектура описана\n- [x] Use-cases задокументированы\n- [x] Метрики определены",
            created_at="2026-03-15T10:00:00Z",
            installation_id=1,
        ),
        files={
            "README.md": "# Project Alpha\n\nСистема рекомендаций для онлайн-магазина.\n\n## Запуск\n\n```bash\ndocker compose up -d\n```\n\n## Архитектура\n\nСм. docs/architecture.md",
            "docs/architecture.md": "# Архитектура\n\n## Компоненты\n\n1. **API Gateway** (FastAPI) — принимает запросы, роутит к сервисам\n2. **Recommendation Service** (Python) — ML модель (collaborative filtering)\n3. **User Service** (PostgreSQL + SQLAlchemy) — профили пользователей\n4. **Redis** — кеш рекомендаций (TTL 1 час)\n\n## Диаграмма\n\n```\nClient → API Gateway → Recommendation Service → Redis\n                     → User Service → PostgreSQL\n```\n\n## Решения\n\n- Collaborative filtering вместо content-based: у нас много данных о поведении\n- Redis для кеша: рекомендации не меняются часто\n- PostgreSQL: ACID для профилей",
            "docs/use-cases.md": "# Use Cases\n\n## UC-1: Получение рекомендаций\n\n**Актор:** Авторизованный пользователь\n**Предусловие:** Пользователь имеет историю покупок (≥5)\n**Основной сценарий:**\n1. Пользователь открывает главную страницу\n2. Система запрашивает рекомендации из Redis\n3. Если кеш пуст — запрос к ML модели\n4. Возвращает топ-10 товаров\n\n**Альтернативный:** Новый пользователь без истории → показываем популярные товары\n\n## UC-2: Обновление профиля\n\n**Актор:** Пользователь\n1. Пользователь меняет предпочтения\n2. Система обновляет профиль в PostgreSQL\n3. Инвалидирует кеш рекомендаций",
            "docs/metrics.md": "# Метрики\n\n| Метрика | Целевое значение | Измерение |\n|---------|------------------|----------|\n| Precision@10 | ≥0.3 | Offline eval на тестовой выборке |\n| p95 latency | ≤200ms | Prometheus + Grafana |\n| Throughput | ≥100 RPS | Load test (k6) |\n| Cache hit rate | ≥80% | Redis metrics |\n\n## SLA\n\n- Uptime: 99.5%\n- Recovery time: ≤5 min (Docker restart)",
        },
        roster_entry={
            "github_username": "perfect-student",
            "full_name": "Иванов Иван",
            "group_id": "ИВТ-1",
            "team_name": "Team Alpha",
            "role": "AI Engineer",
            "topic": "Рекомендательная система",
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
        spec_html="<h2>Lab 2 — AI Engineer</h2><h3>D1: Архитектура</h3><p>Описание компонентов системы, их связей и обоснование выбора.</p><p>Файл: docs/architecture.md</p><h3>D2: Use Cases</h3><p>Сценарии использования с акторами и предусловиями.</p><p>Файл: docs/use-cases.md</p><h3>D3: Метрики</h3><p>Конкретные метрики с целевыми значениями.</p><p>Файл: docs/metrics.md</p><h3>DoD</h3><ul><li>README обновлён</li><li>Архитектура описана</li><li>Use-cases задокументированы</li><li>Метрики определены</li></ul>",
        ground_truth=GroundTruth(
            expected_score_range=(35.0, 50.0),  # из 50 max
            must_find_issues=[],  # идеальная работа, нет проблем
            must_not_miss=["архитектура", "use-case", "метрик"],
            min_criteria_covered=5,
        ),
    )
