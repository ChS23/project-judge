"""Сценарий: лаба с кодом, проект со множеством проблем."""

from judge.models.pr import PRContext

from .base import EvalScenario, GroundTruth

BAD_MAIN_PY = """\
import os
PASSWORD = "admin123"
DB_HOST = "192.168.1.100"

def do_everything(request_data, db_connection, user_id, flag, mode, extra=None):
    # TODO: refactor this later
    if mode == 1:
        result = db_connection.execute("SELECT * FROM users WHERE id = " + str(user_id))
        data = result.fetchall()
        if len(data) > 0:
            user = data[0]
            if flag:
                if extra:
                    print("processing extra")
                    for item in extra:
                        if item.get("type") == "A":
                            db_connection.execute("INSERT INTO logs VALUES ('" + str(item) + "')")
                        elif item.get("type") == "B":
                            db_connection.execute("INSERT INTO logs VALUES ('" + str(item) + "')")
                        else:
                            db_connection.execute("INSERT INTO logs VALUES ('" + str(item) + "')")
                    return {"status": "ok", "data": data}
                else:
                    return {"status": "ok", "data": data}
            else:
                return {"status": "ok", "data": data}
        else:
            return {"status": "not found"}
    elif mode == 2:
        # copy-paste from mode 1
        result = db_connection.execute("SELECT * FROM users WHERE id = " + str(user_id))
        data = result.fetchall()
        if len(data) > 0:
            return {"status": "ok", "data": data, "mode": 2}
        else:
            return {"status": "not found"}
    else:
        return {"status": "error"}

# print("debug")
# print(PASSWORD)
# old_function()
"""

BAD_DOCKERFILE = """\
FROM python:3.99-nonexistent
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD ["python", "main.py"]
"""

BAD_COMPOSE = """\
version: "3"
services:
  app:
    build: .
    ports:
      - "8000:8000"
    depends_on:
      - nonexistent_db
  nonexistent_db:
    image: postgres:999
"""

SANDBOX_REPORT_MOCK = {
    "project_structure": "Плоская структура: main.py, Dockerfile, docker-compose.yml в корне. Нет разделения на модули.",
    "build_status": "fail",
    "build_details": "Dockerfile: base image python:3.99-nonexistent не существует. Build failed.",
    "tests_status": "not_found",
    "tests_output": "Тесты не найдены (нет pytest, unittest или аналогов)",
    "services": [],
    "code_quality_issues": [
        "main.py:2 — захардкоженный пароль PASSWORD = 'admin123'",
        "main.py:3 — захардкоженный IP базы данных",
        "main.py:12 — SQL injection: конкатенация user_id в запрос",
        "main.py:12-44 — функция do_everything на 40+ строк, делает всё",
        "main.py:23-27 — copy-paste: три одинаковых INSERT",
        "main.py:35-42 — copy-paste: дублирование логики mode 1",
        "main.py:46-48 — закомментированный мёртвый код",
    ],
    "architecture_issues": [
        "Весь код в одном файле main.py",
        "Нет разделения на слои (routes, services, models)",
        "Конфигурация захардкожена, не через env",
        "Нет .gitignore",
    ],
    "inline_comments": [
        {
            "path": "main.py",
            "line": 2,
            "body": "Захардкоженный пароль. Используйте переменные окружения.",
        },
        {
            "path": "main.py",
            "line": 12,
            "body": "SQL injection: используйте параметризованные запросы.",
        },
        {
            "path": "main.py",
            "line": 23,
            "body": "Copy-paste: три одинаковых INSERT. Вынесите в функцию.",
        },
    ],
    "issues": [
        "Dockerfile не собирается",
        "Нет тестов",
        "docker-compose ссылается на несуществующий image",
    ],
    "summary": "Проект не собирается. Код содержит критические проблемы безопасности (SQL injection, хардкод паролей), нарушения архитектуры (всё в одном файле), дублирование и мёртвый код.",
}


def bad_code_scenario() -> EvalScenario:
    return EvalScenario(
        name="bad_code",
        description="Лаба 3 с кодом. Проект со множеством проблем: "
        "SQL injection, захардкоженные пароли, copy-paste, нет тестов, Dockerfile не собирается.",
        pr_context=PRContext(
            repo="vstu-sii/test-eval-repo",
            pr_number=5,
            pr_url="https://github.com/vstu-sii/test-eval-repo/pull/5",
            sender="bad-coder",
            branch="lab3-fullstack-deliverables",
            head_sha="eee555",
            body="## DoD\n- [x] Код написан\n- [ ] Тесты написаны\n- [ ] Docker работает",
            created_at="2026-03-25T10:00:00Z",
            installation_id=1,
        ),
        files={
            "main.py": BAD_MAIN_PY,
            "Dockerfile": BAD_DOCKERFILE,
            "docker-compose.yml": BAD_COMPOSE,
            "requirements.txt": "flask\npsycopg2",
        },
        roster_entry={
            "github_username": "bad-coder",
            "full_name": "Кодов Код",
            "group_id": "ИВТ-2",
            "team_name": "Team Epsilon",
            "role": "Fullstack",
            "topic": "Управление пользователями",
        },
        rubrics=[
            {
                "lab_id": "3",
                "deliverable_id": "D1",
                "role": "Fullstack",
                "criterion": "Код: качество и структура",
                "max_score": "15",
                "weight": "1",
            },
            {
                "lab_id": "3",
                "deliverable_id": "D1",
                "role": "Fullstack",
                "criterion": "Код: безопасность",
                "max_score": "10",
                "weight": "1",
            },
            {
                "lab_id": "3",
                "deliverable_id": "D2",
                "role": "Fullstack",
                "criterion": "Тесты: покрытие",
                "max_score": "10",
                "weight": "1",
            },
            {
                "lab_id": "3",
                "deliverable_id": "D3",
                "role": "Fullstack",
                "criterion": "Docker: сборка и запуск",
                "max_score": "15",
                "weight": "1",
            },
        ],
        deadline="2026-03-28T23:59:00Z",
        spec_html="<h2>Lab 3 — Fullstack</h2><h3>D1: Код</h3><p>Рабочий код с тестами.</p><h3>D2: Тесты</h3><p>Unit тесты.</p><h3>D3: Docker</h3><p>Dockerfile + docker-compose.</p><h3>DoD</h3><ul><li>Код написан</li><li>Тесты написаны</li><li>Docker работает</li></ul>",
        ground_truth=GroundTruth(
            expected_score_range=(0.0, 15.0),
            must_find_issues=["SQL injection", "пароль", "copy-paste", "не собирается"],
            must_not_miss=["безопасност", "injection", "docker"],
            should_call_review_code=True,
            min_criteria_covered=4,
        ),
        sandbox_report=SANDBOX_REPORT_MOCK,
        uses_sandbox=True,
    )
