# Архитектура системы

```
GitHub PR (открыт студентом)
    ↓
GitHub Actions (webhook trigger)
    ↓
Orchestrator Agent (LangGraph + GLM-4.7)
    │
    ├── [1] Google Sheets Reader
    │     → студент по username → роль, команда, группа
    │     → дедлайн для lab_id + group_id
    │     → рубрики для lab_id + deliverable_id
    │
    ├── [2] Spec Fetcher
    │     → GET сайт/materials/labs/lab{N}
    │     → парсинг DoD критериев и ожидаемых файловых путей
    │
    ├── [3] Artifacts Agent
    │     → проверка наличия файлов по путям из спецификации
    │     → парсинг DoD чеклиста из PR description
    │
    ├── [4] Content Reviewer
    │     → LLM оценка содержимого по рубрикам из Sheets
    │     → детект prompt injection паттернов
    │
    ├── [5] Sandbox Agent (только Lab 4+)
    │     → E2B v2: sandbox.git.clone → docker-compose up → health checks
    │     → HTTP check demo links (3 retry)
    │
    └── [6] Deadline Agent
          → расчёт penalty_coefficient
    ↓
Results Aggregator
    ├── Комментарий в PR (markdown отчёт с оценкой по критериям)
    └── Запись в Google Sheets (вкладка results)
```

## Агенты

**Artifacts Agent**
- Читает diff PR → список файлов
- Сравнивает с ожидаемыми путями из спецификации сайта
- Парсит `- [x]` / `- [ ]` из PR description
- Результат: `{files_present: [], files_missing: [], dod_checked: N, dod_total: M}`

**Content Reviewer**
- Получает текст каждого артефакта
- Sanitization перед передачей в LLM
- Оценивает по рубрикам из Sheets (конкретность, полнота, измеримость)
- Результат: `{criterion: score}` по каждому deliverable

**Sandbox Agent** (Lab 4+)
- E2B sandbox v2 на каждый PR, изолированно
- `sandbox.git.clone()` → `docker-compose up` → health checks → `pytest`
- Точка входа стандартизирована: `docker-compose up` обязателен по DoD
- Три уровня: воспроизводимость → работоспособность → качество тестов
- Таймаут: 10 минут, streaming вывода команд
- Результат: `{build: pass/fail, tests: N/M, demo_alive: bool, errors: [...]}`

**Deadline Agent**
- Читает `pr.created_at` из GitHub API
- Читает дедлайн из Google Sheets
- Считает `penalty_coefficient`
- Результат: `{days_late: N, coefficient: 0.X}`
