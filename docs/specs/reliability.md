# Reliability & Resilience Spec

## LLM Unavailability Protection

### Current State

| Scenario | Handling | Impact |
|----------|----------|--------|
| Z.AI 5xx | LangChain raises → Taskiq retries once → `grading-error` label | PR not graded, instructor notified |
| Z.AI 429 (rate limit) | LangChain built-in exponential backoff | Transparent retry, added latency |
| Z.AI timeout | `httpx.ReadTimeout` → retry → error label | Same as 5xx |
| Z.AI returns invalid JSON | `with_structured_output` → `OutputParserException` | Agent gets error in ToolMessage, may retry |
| Z.AI returns refusal | Empty/short response | Agent interprets as tool failure, tries next step |

### Recommended Improvements

1. **Circuit breaker**: после 3 consecutive failures за 5 min — перестать принимать новые tasks, drain queue
2. **Fallback LLM**: если Z.AI недоступен >5 min — switch на backup provider (env: `ZAI_FALLBACK_BASE_URL`)
3. **Dead letter queue**: failed tasks после max retries → отдельная Redis queue для ручной обработки
4. **Health degradation**: `/health` возвращает 503 если последние N LLM calls failed

## Failure Cascade Prevention

### Webhook → Worker

```
Webhook receives event
  → Signature valid? No → 401 (instant, no side effects)
  → Enqueue to Redis? Fail → 500 (Redis down)
    → Recovery: Redis restart, webhook resend by GitHub (auto-retry)
```

GitHub автоматически повторяет webhooks при 5xx (до 3 раз с exponential backoff).

### Worker → Agent

```
Worker dequeues task
  → build_agent() fails → ImportError, config error
    → Immediate failure, error label, no retry (broken code)
  → ainvoke() fails mid-execution
    → Taskiq retry once
    → If retry fails → error comment + grading-error label
```

### Agent → Tools

```
Agent calls tool
  → Tool raises exception → ToolNode catches, returns error in ToolMessage
    → Agent sees error, can retry or skip
  → Tool hangs → No timeout per-tool (gap!)
    → Mitigated by: recursion_limit=30 (total steps), sandbox_timeout=600s
```

### Sub-agent → Sandbox

```
review_code() called
  → E2B API down → "E2B sandbox не настроен" skip message
  → Sandbox created, clone fails → Return error, sandbox killed
  → Sandbox created, agent loop runs
    → Command hangs → per-command timeout (default 60s)
    → Agent loops too many times → recursion_limit (inherits from parent? No — sub-agent has own limit)
    → Sandbox timeout → E2B kills sandbox after 600s
  → finally: sandbox.kill() → guaranteed cleanup
```

## Resource Utilization

### Current Resource Usage

| Resource | Typical | Peak | Limit |
|----------|---------|------|-------|
| Worker memory | ~200MB | ~500MB (large PR) | Container memory limit |
| Redis memory | ~10MB | ~50MB (burst queue) | No limit set (gap) |
| LLM tokens per PR | ~10K | ~50K (many files + sandbox) | No budget enforcement |
| Sandbox CPU | 1 vCPU | 2 vCPU | E2B plan limit |
| Sandbox disk | ~500MB | ~2GB (large repos) | E2B plan limit |
| Network (GitHub API) | ~20 req/PR | ~100 req/PR | 5000 req/h |

### Optimization Opportunities

1. **LLM token budget**: установить max_tokens на LLM calls, прерывать если agent расходует >50K tokens
2. **Parallel tool calls**: LangGraph поддерживает — если LLM вернёт несколько tool_calls, ToolNode выполнит их параллельно
3. **Selective file reading**: агент сначала видит список файлов (check_artifacts), затем читает только релевантные
4. **Sandbox template**: pre-baked E2B template с Docker, pytest, node — экономит 30-60s на setup
5. **Redis memory limit**: `maxmemory 100mb` + `maxmemory-policy allkeys-lru`

## Idempotency

| Operation | Idempotent? | Risk |
|-----------|------------|------|
| post_comment | No | Duplicate comments on retry |
| write_results | No | Duplicate rows in Sheets |
| add_label | Yes | GitHub ignores duplicate labels |
| escalate | Yes | Same as add_label |
| read_roster | Yes | Read-only |
| sandbox operations | N/A | Sandbox destroyed after each run |

### Mitigation

- **Deduplication key**: `{repo}:{pr_number}:{head_sha}` — check if already graded before starting
- Текущая реализация: нет (PoC gap). Worker может заградить один PR дважды если webhook пришёл дважды.

## Graceful Degradation Matrix

| Component Down | Impact | Degradation |
|----------------|--------|-------------|
| Z.AI | Cannot grade | Retry once → error label → manual review |
| GitHub API | Cannot read files / post results | Retry once → error label |
| Google Sheets | Cannot resolve student / write results | Grade without roster info, skip results write |
| E2B | Cannot run sandbox | Skip code review, grade documents only |
| Langfuse | Cannot trace | Silent skip — grading unaffected |
| Redis | Cannot enqueue/dequeue tasks | Webhook returns 500, GitHub retries |
| Lab spec site | Cannot fetch spec | Agent uses branch name for lab/role, partial grading |

## Recommended Production Hardening

### Priority 1 (Before semester start)

- [ ] Deduplication: skip if `graded` label already present for same `head_sha`
- [ ] Redis `maxmemory` config
- [ ] LLM token budget per agent run
- [ ] External uptime monitor for `/health`

### Priority 2 (During semester)

- [ ] Circuit breaker for Z.AI API
- [ ] Dead letter queue for failed tasks
- [ ] Prometheus metrics export from worker
- [ ] Sentry integration for error tracking

### Priority 3 (Post-PoC)

- [ ] Fallback LLM provider
- [ ] Worker auto-scaling (multiple instances)
- [ ] Redis persistence (AOF)
- [ ] E2B sandbox template (pre-baked)
- [ ] Automated eval pipeline (agent scores vs instructor scores)
