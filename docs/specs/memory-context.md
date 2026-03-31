# Memory & Context Spec

## Session State

Каждый PR обрабатывается в изолированной сессии. Нет shared state между запусками.

### Agent State

```python
class MessagesState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
```

Единственное поле — `messages`. Весь собранный контекст (roster, spec, scores) передаётся через `ToolMessage` в цепочке сообщений.

### Sub-agent State

| Sub-agent | State | Isolation |
|-----------|-------|-----------|
| evaluate_content | `MessagesState` (single LLM call) | Полная: свой system prompt, не видит историю основного агента |
| review_code | `MessagesState` (tool-use loop) | Полная: свой system prompt, свои tools (sandbox), не видит основного агента |

## Memory Policy

| Aspect | Policy |
|--------|--------|
| Cross-attempt memory (same PR) | `read_past_reviews` — читает прошлые комментарии бота из PR |
| Cross-PR memory (different PRs) | None — каждый PR независим |
| Cross-session memory | None — worker stateless |
| In-session memory | Tool results в `messages` |
| Persistent storage | Google Sheets (results), GitHub (comments, labels) |

### Cross-attempt Context (Recheck)

При перепроверке агент вызывает `read_past_reviews()` первым шагом:
- Читает все комментарии бота в PR (фильтр: `[bot]` suffix + "Результат" keyword)
- Каждый комментарий truncated до 3000 chars
- Агент сравнивает текущее состояние с прошлыми замечаниями
- Источник данных: GitHub PR comments (not a separate store)

### Почему нет cross-PR memory

- PoC scope — не оправдана сложность
- Каждый PR самодостаточен: roster + spec + artifacts
- Риск data leakage между студентами при shared memory

### Когда может понадобиться

- Отслеживание прогресса студента по лабам (Lab 1 → Lab 4): добавить `read_past_results(sender)` из Sheets
- Детекция плагиата между PR разных студентов
- Обучение на ошибках грейдинга (instructor feedback loop)

## Context Budget

### Main Agent

| Source | Max Size | Notes |
|--------|----------|-------|
| System prompt | ~4000 tokens | Fixed, includes report template |
| PR body | 2000 chars | Truncated in system prompt |
| Tool results (per call) | Varies | See below |
| Total context | ~30K tokens typical | Зависит от числа deliverables |

### Per-tool Context Contribution

| Tool | Typical Output | Max Output |
|------|---------------|------------|
| read_roster | ~200 chars | ~500 chars |
| fetch_spec | ~2000 chars | 8000 chars (raw_text) |
| check_artifacts | ~500 chars | ~2000 chars |
| read_file | ~5000 chars | 15000 chars |
| parse_dod | ~200 chars | ~500 chars |
| check_deadline | ~150 chars | ~300 chars |
| evaluate_content | ~1000 chars | ~3000 chars |
| review_code | ~2000 chars | ~5000 chars (SandboxReport JSON) |

### Sandbox Sub-agent

| Source | Max Size |
|--------|----------|
| System prompt (REVIEWER_PROMPT) | ~2000 tokens |
| run_command stdout | 5000 chars |
| run_command stderr | 3000 chars |
| read_file | 10000 chars |
| list_files | 5000 chars |
| Format call (all messages) | Accumulated |

## Cache Strategy

| Cache | Key | TTL | Scope | Invalidation |
|-------|-----|-----|-------|-------------|
| Installation token | `installation_id` | 55 min | Process-global dict | Auto (TTL) |
| Roster | `(spreadsheet_id, "roster")` | 300s | Per-worker process | Auto (TTL) |
| Rubrics | `(spreadsheet_id, lab_id, role)` | 300s | Per-worker process | Auto (TTL) |
| Deadlines | `(spreadsheet_id, lab_id, group_id)` | 300s | Per-worker process | Auto (TTL) |

### Cache Limitations (PoC)

- In-memory `TTLCache` — lost on worker restart
- No distributed cache — multiple workers have independent caches
- No explicit invalidation — instructor changes take up to 5 min to propagate
