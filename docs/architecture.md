# Архитектура системы

## Agent loop (паттерн Claude Code)

Агент работает как tool use loop — LLM сам решает какие tools вызвать, в каком порядке, сколько раз. Адаптируется к разным лабам и проектам без хардкода.

```
GitHub PR webhook
    ↓
Granian ASGI → gidgethub verify + route → Taskiq Redis queue → 202
    ↓
Taskiq worker
    ↓
LangGraph StateGraph (low-level):
    ┌─────────────────────────────────────────┐
    │  agent node (GLM-4.7 + bound tools)     │
    │      ↓                                  │
    │  tool_calls? ──yes──→ ToolNode          │
    │      │                    │              │
    │      no                   └──→ agent     │
    │      ↓                                  │
    │     END (финальный отчёт)               │
    └─────────────────────────────────────────┘
```

Реализация: `StateGraph` + `ToolNode` + `tools_condition` из LangGraph.

## Tools

Агент имеет доступ к набору tools. Каждый tool — async функция с `@tool` декоратором.

**Детерминированные tools:**

| Tool | Что делает | LLM внутри? |
|---|---|---|
| `read_roster(username)` | Lookup студента в Google Sheets → группа, роль, команда | Нет |
| `fetch_spec(lab_id)` | HTTP fetch спецификации лабы с сайта курса | Нет |
| `check_artifacts(repo, pr)` | Список файлов в PR diff, сравнение с ожидаемыми | Нет |
| `parse_dod(pr_body)` | Парсинг `[x]`/`[ ]` чеклиста из описания PR | Нет |
| `check_deadline(created_at, deadline)` | Расчёт penalty_coefficient | Нет |
| `post_comment(repo, pr, body)` | Комментарий в PR через GitHub API | Нет |
| `write_results(...)` | Запись результатов в Google Sheets | Нет |

**Sub-agents (tool внутри которого отдельный LLM):**

| Tool | Что делает |
|---|---|
| `evaluate_content(text, criteria)` | Оценка качества документа по рубрикам. Отдельный LLM вызов с промптом для оценки. Изолированный контекст |
| `run_sandbox(repo, branch)` | E2B sandbox: clone → docker-compose → health checks → pytest. Sub-agent разбирается с ошибками сам |

## Почему tool use loop, а не статический граф

- Каждая лаба другая (документы / код / docker / demo)
- Каждый студенческий проект уникален
- Агент адаптируется: если sandbox упал — проверяет документы, если файлов нет — не оценивает контент
- Настоящий агент (требование курса)
- Audit trail — полная история рассуждений для апелляций

## Системный промпт

Промпт направляет агента:
- Роль: автоматический грейдер студенческих проектов
- Контекст PR: repo, branch, sender, created_at
- Правила оценки: формула штрафов, шкала баллов
- Формат отчёта: markdown таблица с критериями
- Ограничения: не мержить PR, не удалять файлы
