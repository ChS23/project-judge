# System Design Document

## 1. Key Architectural Decisions

| # | Decision | Rationale |
|---|----------|-----------|
| AD-1 | Tool-use loop agent (не статический граф) | Разные лабы требуют разных шагов; агент адаптируется |
| AD-2 | Deterministic tools для проверяемого, LLM для непроверяемого | Файловые проверки, дедлайны, DoD — regex/формулы. Качество документов — LLM |
| AD-3 | Sub-agents для изолированных задач | `evaluate_content` и `review_code` имеют свой промпт, tools и context window |
| AD-4 | GitHub App, не Actions | Полный контроль workflow, нет ограничений на compute time, не расходует минуты студентов |
| AD-5 | Taskiq + Redis для async processing | Webhook отвечает 202 мгновенно, грейдинг идёт в фоне, retry при сбоях |
| AD-6 | E2B Sandbox, не Docker-in-Docker | Firecracker microVM — безопасная изоляция, нет побега в хост |
| AD-7 | PR created_at для дедлайнов | Immutable через GitHub API, нельзя подменить (в отличие от commit date) |
| AD-8 | No irreversible actions | Агент никогда не мёрджит PR, не удаляет файлы, не модифицирует репо |
| AD-9 | Penalty coefficient, не вычитание баллов | Единообразная формула для всех лаб: `final = raw_score * coeff` |
| AD-10 | Inline PR review comments из sandbox | Конкретная обратная связь на строках кода, а не абстрактные замечания |
| AD-11 | Recheck через Q&A агент, не отдельный роутинг | Q&A агент сам классифицирует намерение из контекста и вызывает `trigger_recheck` — не нужен отдельный классификатор |
| AD-12 | Cross-attempt context через PR comments | Прошлые оценки читаются из комментариев бота в том же PR — не нужен отдельный storage |

## 2. Module Map

```
judge/
├── webhook/          # ASGI app, signature verification, event routing
│   ├── app.py        # Granian entrypoint, /health, /webhook
│   └── router.py     # PR events → task dispatch
├── tasks/            # Taskiq async workers
│   ├── broker.py     # Redis-backed ListQueueBroker
│   ├── grade_pr.py   # Main grading pipeline
│   └── answer_question.py  # Q&A sub-agent for PR comments
├── agent/            # LangGraph orchestration
│   ├── graph.py      # StateGraph builder, Langfuse tracing
│   ├── prompt.py     # System prompt factory
│   └── tools/        # 12 tools (see below)
├── github/           # GitHub App integration
│   ├── auth.py       # JWT + installation token caching
│   ├── client.py     # API calls: comments, reviews, files, labels
│   └── helpers.py    # Branch name parser
├── llm/              # LLM abstraction
│   ├── client.py     # ChatOpenAI wrapper (Z.AI endpoint)
│   └── sanitize.py   # Injection detection + structural isolation
├── sheets/           # Google Sheets integration
│   ├── client.py     # Roster, rubrics, deadlines, results
│   └── cache.py      # In-memory TTL cache
├── models/           # Pydantic data models
│   ├── pr.py         # PRContext
│   ├── roster.py     # StudentRecord
│   └── rubric.py     # RubricCriterion, LabSpec
└── settings.py       # Pydantic Settings, env-based config
```

### Tool Registry

| Tool | Type | Description |
|------|------|-------------|
| `read_past_reviews` | deterministic | Чтение прошлых оценок бота из PR comments |
| `read_roster` | deterministic | Lookup студента в Google Sheets |
| `fetch_spec` | deterministic | Парсинг спецификации лабы (HTML → structured) |
| `check_artifacts` | deterministic | Diff файлов PR vs ожидаемых |
| `read_file` | deterministic | Чтение файла из PR branch через GitHub API |
| `parse_dod` | deterministic | Подсчёт [x]/[ ] чекбоксов в PR body |
| `check_deadline` | deterministic | Расчёт штрафного коэффициента |
| `evaluate_content` | sub-agent | LLM-оценка документа по рубрикам |
| `review_code` | sub-agent | Code review в E2B sandbox (tool-use loop) |
| `post_comment` | write | Публикация markdown-отчёта в PR |
| `escalate` | write | Label `needs-review` + причина |
| `write_results` | write | Запись оценок в Google Sheets |

**Q&A Agent Tools (answer_question):**

| Tool | Type | Description |
|------|------|-------------|
| `check_artifacts` | deterministic | Список файлов PR |
| `read_file` | deterministic | Чтение файла из PR branch |
| `fetch_spec` | deterministic | Спецификация лабы |
| `trigger_recheck` | write | Запуск полного перегрейда PR в фоне |

## 3. Main Workflow

```
[GitHub PR opened/synchronized]          [PR comment from student]
       │                                         │
       ▼                                         ▼
[Webhook: verify signature]              [Webhook: verify signature]
       │                                         │
       ▼                                         ▼
[Router: enqueue grade_pr]               [Router: enqueue answer_question]
       │                                         │
       ▼                                         ▼
[Taskiq Worker]                          [Q&A Agent]
       │                                    │          │
       ▼                                    ▼          ▼
[build_agent]                          [question]  [recheck intent]
       │                                    │          │
       ▼                                    ▼          ▼
┌──────────────────────────────┐     [reply +    [trigger_recheck]
│     AGENT TOOL-USE LOOP      │      hint         │
│                              │      counter]     │
│  1. read_past_reviews()      │◄──────────────────┘
│     → prошлые оценки (если   │
│       есть — это recheck)    │
│                              │
│  2. read_roster(sender)      │
│     → student info, role     │
│                              │
│  3. fetch_spec(lab_id, role) │
│     → deliverables, DoD      │
│                              │
│  4. check_artifacts(files)   │
│     → present/missing        │
│                              │
│  5. read_file(path) × N     │
│                              │
│  6. parse_dod(pr_body)       │
│                              │
│  7. check_deadline()         │
│     → penalty coefficient    │
│                              │
│  8. evaluate_content() × N   │
│     → scores per criterion   │
│                              │
│  9. review_code() [if code]  │
│     → SandboxReport JSON     │
│     → inline PR comments     │
│                              │
│ 10. post_comment(report)     │
│     → recheck: diff с прошлой│
│       оценкой                │
│                              │
│ 11. write_results(scores)    │
│                              │
│ 12. escalate() [if needed]   │
└──────────────────────────────┘
       │
       ▼
[Add "graded" label, task complete]
```

## 4. State / Memory / Context Handling

### Agent State

```python
class MessagesState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
```

- **Единственное поле** — `messages`. Весь контекст передаётся через tool results в сообщениях.
- Cross-attempt context: `read_past_reviews` читает прошлые комментарии бота из PR — агент видит историю оценок.
- Нет persistent memory между разными PR — каждый PR обрабатывается независимо.
- `recursion_limit=30` — hard stop для зацикливания.

### Sub-agent State

- `evaluate_content`: single LLM call, no tools, isolated context.
- `review_code`: full tool-use loop (`run_command`, `read_file`, `list_files`) → format node (`with_structured_output`) → `SandboxReport`.

### Context Budget

| Component | Limit |
|-----------|-------|
| PR body | 2000 chars (truncated in system prompt) |
| File content | 15000 chars per file (read_file) |
| Spec raw text | 8000 chars (fetch_spec) |
| Sandbox stdout | 5000 chars per command |
| Sandbox stderr | 3000 chars per command |
| Sandbox read_file | 10000 chars |
| evaluate_content | 10000 chars document text |

### Session Isolation

- Каждый PR = отдельный `ainvoke()` с чистым state.
- Taskiq worker может обрабатывать несколько PR параллельно — state не разделяется.
- Google Sheets cache (`TTLCache`) — in-memory, per-worker process, TTL 300s.

## 5. Retrieval Contour

Система не использует vector search / RAG. Все данные получаются через детерминированные API:

| Source | Access | Caching |
|--------|--------|---------|
| Google Sheets (roster) | `sheets.read_roster()` | 300s TTL |
| Google Sheets (rubrics) | `sheets.read_rubrics()` | 300s TTL |
| Google Sheets (deadlines) | `sheets.read_deadline()` | 300s TTL |
| Lab spec page | HTTP GET + HTML parse | None (stateless) |
| PR files (list) | GitHub REST API | None |
| PR files (content) | GitHub REST API | None |
| PR diff | GitHub REST API | None (per-review call) |
| Past reviews (bot comments) | GitHub REST API | None (per-grading call) |

### Future: если появится RAG

Кандидаты для индексации: спецификации лаб (6 лаб × 5 ролей), типовые ошибки студентов, FAQ. Объём ~50 документов — vector store overkill, достаточно structured fetch.

## 6. Tool / API Integrations

| Integration | Protocol | Auth | Rate Limits | Timeout |
|-------------|----------|------|-------------|---------|
| Z.AI (GLM-4.7) | OpenAI-compatible REST | API key in header | Provider-dependent | 120s default |
| GitHub API | REST v3 | JWT → installation token (55 min TTL) | 5000 req/h per installation | 30s httpx |
| Google Sheets | REST (aiogoogle) | Service account JSON | 300 req/min | 30s |
| E2B Sandbox | REST + WebSocket | API key | 20 parallel sandboxes | 600s (configurable) |
| Lab spec pages | HTTP GET | None (public) | N/A | 30s |
| Langfuse | REST | Public + secret key | N/A (async flush) | Non-blocking |

## 7. Failure Modes, Fallbacks, and Guardrails

### 7.1 LLM Unavailability

| Scenario | Detection | Response |
|----------|-----------|----------|
| Z.AI API down (5xx) | `httpx.HTTPStatusError` | Taskiq retry (max_retries=1), затем `grading-error` label |
| Z.AI rate limit (429) | HTTP 429 | LangChain built-in exponential backoff |
| Z.AI timeout | `httpx.ReadTimeout` | Retry once, then error comment in PR |
| Malformed LLM response | `ValidationError` on parse | Graceful degradation: return raw text |
| LLM hallucination (tool) | Tool raises exception | ToolNode returns error message, agent retries |

### 7.2 External Service Failures

| Service | Failure | Fallback |
|---------|---------|----------|
| GitHub API | 401/403 | Re-generate installation token (cache miss) |
| GitHub API | 422 on review | Filter invalid inline comments, post as regular comment |
| GitHub API | Rate limit | Exponential backoff in gidgethub |
| Google Sheets | Unavailable | Roster lookup fails → agent continues without student info |
| Google Sheets | Write fails | Error logged, grade still posted as PR comment |
| E2B Sandbox | API key missing | `review_code` returns skip message, grading continues |
| E2B Sandbox | Timeout | `sandbox.kill()` in `finally` block, return partial report |
| Lab spec page | 404/unreachable | `fetch_spec` returns error, agent uses branch name for lab ID |

### 7.3 Guardrails

| Guardrail | Implementation |
|-----------|---------------|
| Prompt injection | 13 regex patterns + structural isolation (`--- BEGIN/END STUDENT DOCUMENT ---`) |
| Sandbox escape | E2B Firecracker microVM, no network to host, auto-kill on timeout |
| Command injection | `shlex.quote()` in `list_files`, sandbox is disposable anyway |
| Infinite loop | `recursion_limit=30` in agent graph |
| Large payloads | Webhook body ≤1MB, file content ≤15K chars, sandbox output ≤5K chars |
| Token leakage | Installation tokens cached 55 min (expire at 60), no tokens in logs |
| No irreversible actions | Agent can only: post comments, add labels, write to Sheets |
| Escalation | Auto-label `needs-review` on: 40-60% score, injection, sandbox errors, disagreement >30% |

### 7.4 Resource Protection

| Resource | Limit | Enforcement |
|----------|-------|-------------|
| Agent iterations | 30 steps max | `recursion_limit=30` |
| Sandbox lifetime | 600s | `Sandbox(timeout=600)` + `finally: sandbox.kill()` |
| Sandbox concurrency | 20 (E2B plan) | E2B platform-enforced |
| Webhook body size | 1 MB | `_read_body()` truncation |
| Task retries | 1 | `max_retries=1` in Taskiq |
| Q&A hints per PR | 5 | Counter in `answer_question` |

## 8. Technical and Operational Constraints

### 8.1 Latency

| Operation | Expected | Worst Case |
|-----------|----------|------------|
| Webhook → task enqueue | <100ms | 500ms |
| Full grading (docs only) | 30-60s | 120s |
| Full grading (with sandbox) | 120-300s | 600s |
| Sub-agent: evaluate_content | 5-15s | 60s |
| Sub-agent: review_code | 60-180s | 600s |
| GitHub API call | 100-500ms | 5s |
| Google Sheets read | 200-800ms | 3s |
| Target end-to-end | <5 min | <10 min |

### 8.2 Cost (per PR grading)

| Component | Estimated |
|-----------|-----------|
| LLM calls (main agent, ~10 turns) | ~0.01-0.05 USD |
| LLM calls (evaluate_content, 1-3 calls) | ~0.01-0.03 USD |
| LLM calls (review_code, ~5-15 turns + format) | ~0.02-0.08 USD |
| E2B sandbox (5 min) | ~0.01 USD |
| **Total per PR** | **~0.05-0.17 USD** |
| **Per semester (200 PRs)** | **~10-34 USD** |

### 8.3 Reliability Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| Uptime (webhook receiver) | >99% | Healthcheck + Docker restart |
| Grading completion rate | >95% | `graded` / `grading-error` labels ratio |
| False negative rate | <10% | Manual review sample |
| Grading accuracy | >85% | Correlation with instructor scores |

### 8.4 Scaling Limits

- **Redis**: single instance, no HA — single point of failure (acceptable for PoC)
- **Worker**: single process, sequential task execution — throughput ~10-20 PRs/hour
- **Sheets API**: 300 req/min shared across all workers
- **E2B**: 20 concurrent sandboxes (plan limit), ~5 min each
- **LLM**: Z.AI rate limits TBD — no public documentation
