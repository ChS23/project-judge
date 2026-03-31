# Observability & Evals Spec

## Tracing (Langfuse)

### What is Traced

| Trace | Content |
|-------|---------|
| Agent run | Full conversation: system prompt → tool calls → responses → final output |
| LLM calls | Model, tokens in/out, latency, tool definitions |
| Tool calls | Name, arguments, return value, duration |
| Sub-agent calls | Nested traces for evaluate_content, review_code |

### Configuration

```python
CallbackHandler()  # from langfuse.langchain
config["run_name"] = f"grade-pr-{repo_name}-{pr_number}"
config["metadata"] = {repo, pr_number, sender, branch}
```

### Trace Metadata

| Field | Value |
|-------|-------|
| `run_name` | `grade-pr-{repo_short}-{pr_number}` |
| `repo` | Full repo name |
| `pr_number` | PR number |
| `sender` | GitHub username |
| `branch` | PR branch name |

### Когда Langfuse недоступен

- `_langfuse_handler()` возвращает `None` если ключи не настроены
- Callback не добавляется → грейдинг продолжается без трейсов
- Langfuse отправляет трейсы асинхронно — не блокирует основной flow
- Если Langfuse падает после подключения — трейсы теряются, грейдинг не затрагивается

## Structured Logging (structlog)

### Events Logged

| Event | Level | Fields |
|-------|-------|--------|
| `installation_token_acquired` | info | installation_id |
| `review_comments_filtered` | info | total, valid, dropped |
| `grade_pr_start` | info | repo, pr_number, sender |
| `grade_pr_complete` | info | repo, pr_number, duration |
| `grade_pr_error` | error | repo, pr_number, error |
| `webhook_received` | info | event, action |
| `webhook_signature_invalid` | warning | — |

### Log Policy (from governance.md)

- No full student document text in logs
- GitHub usernames are pseudonymous (not PII in context)
- PR metadata (dates, branch names, file names) — logged freely
- Sandbox output — truncated in tool results, not logged separately

## Metrics (Future / PoC Gap)

### Ключевые метрики для мониторинга

| Metric | Source | Target |
|--------|--------|--------|
| Grading success rate | `graded` vs `grading-error` labels | >95% |
| Grading latency (e2e) | Langfuse trace duration | <5 min |
| LLM call latency (p95) | Langfuse span duration | <30s |
| Sandbox timeout rate | review_code error returns | <5% |
| Inline comments dropped | `review_comments_filtered` log | <30% |
| Escalation rate | `needs-review` label count | 10-20% |
| Q&A hint usage | answer_question counter | Informational |

### Текущая реализация мониторинга

| What | How | Gap |
|------|-----|-----|
| LLM call metrics | Langfuse dashboard | No alerting |
| Task success/failure | Labels on PR | No aggregated dashboard |
| Webhook health | `/health` endpoint | No external uptime monitor |
| Redis health | Docker healthcheck | No metrics export |
| Error tracking | structlog to stdout | No aggregation (Sentry etc.) |

### Рекомендации для production

1. **Prometheus + Grafana**: export task metrics (success/fail/duration) из worker
2. **Sentry**: error tracking с context (PRContext, tool name)
3. **Uptime monitor**: external ping to `/health` каждые 60s
4. **Redis monitoring**: `redis-cli info` metrics или Redis Exporter
5. **Alert rules**: grading error rate >10%, LLM latency p95 >60s, webhook 5xx rate

## Evaluation Strategy

### Automated Evals (Future)

| Eval | Method | Frequency |
|------|--------|-----------|
| Grading accuracy | Compare agent scores vs instructor scores | Weekly batch |
| Score distribution | Histogram of final scores per lab | Per lab deadline |
| Injection resistance | Test prompts in fake PRs | On prompt changes |
| Sandbox reliability | % of successful sandbox runs | Continuous |

### Manual Evals (Current)

| Eval | Method |
|------|--------|
| Spot check | Instructor reviews random 10% of graded PRs |
| Escalation review | Instructor reviews all `needs-review` PRs |
| Student complaints | `review-requested` label triggers manual re-check |

### Guardrail Evals

| Guardrail | Test |
|-----------|------|
| Injection detection | 13 regex patterns, tested against known payloads |
| Score bounds | Final score ≥ 0, ≤ max_score (enforced by rubric structure) |
| No irreversible actions | Audit: agent only calls post_comment, add_label, write_results |
| Sandbox isolation | E2B Firecracker guarantees, no custom networking |
