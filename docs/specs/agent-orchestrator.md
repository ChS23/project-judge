# Agent / Orchestrator Spec

## Graph Structure

```
START → agent → tools_condition → tools → agent → ... → END
                                ↘ (no tool_calls) → END
```

- **Pattern**: `StateGraph(MessagesState)` + `ToolNode` + `tools_condition`
- **State**: `messages: list[AnyMessage]` (единственное поле)
- **LLM**: GLM-4.7 via Z.AI, temperature=0.1, tools bound через `bind_tools()`

## Step Rules

Агент получает system prompt с рекомендованным порядком (12 шагов), но **сам решает** какие tools вызвать и в каком порядке. Это design decision — разные лабы требуют разных проверок.

### Обязательные шаги (всегда)

1. `read_past_reviews` — проверка прошлых оценок (первый шаг!)
2. `read_roster` — идентификация студента
3. `fetch_spec` — получение критериев
4. `post_comment` — публикация результата

### Условные шаги

| Условие | Tool |
|---------|------|
| Лаба содержит документы | `evaluate_content` (per deliverable) |
| Лаба содержит код | `review_code` |
| Score 40-60% / injection / sandbox error | `escalate` |

## Recheck Flow

При перепроверке (triggered через Q&A `trigger_recheck` или `synchronize` webhook):

1. `read_past_reviews()` возвращает прошлые оценки бота
2. Агент грейдит заново, но в отчёте:
   - Отмечает что исправлено vs не исправлено
   - Не дублирует одинаковые комментарии
   - Повышает баллы за исправленные критерии

## Q&A Agent

Отдельный агент для ответов на комментарии студентов в PR.

- **Trigger**: Любой `issue_comment` в PR (не от бота)
- **Graph**: `StateGraph(MessagesState)` + `ToolNode` + `tools_condition`
- **Tools**: `check_artifacts`, `read_file`, `fetch_spec`, `trigger_recheck`
- **Hint limit**: 5 подсказок на PR (маркер `<!-- project-judge:hint -->`)
- **Recheck**: Если студент просит перепроверку, Q&A вызывает `trigger_recheck` → `grade_pr.kiq(pr)` в фоне. Не расходует лимит хинтов.
- **Context**: Получает последний grading comment бота для контекста

## Stop Conditions

| Condition | Mechanism |
|-----------|-----------|
| Agent решил закончить | Нет `tool_calls` в response → `tools_condition` → END |
| Слишком много итераций | `recursion_limit=30` → `GraphRecursionError` |
| LLM недоступен | Exception → Taskiq retry → `grading-error` label |

## Retry / Fallback

| Level | Strategy |
|-------|----------|
| Tool error | Agent получает error в ToolMessage, может попробовать другой подход |
| Task error | Taskiq `retry_on_error=True, max_retries=1` |
| After max retries | Post error comment, add `grading-error` label |

## Sub-agents

### evaluate_content
- **Trigger**: Agent calls `evaluate_content(document_text, criteria)`
- **Graph**: Single node, no tools, no loop
- **Input**: Sanitized text + injection warnings
- **Output**: Markdown table with scores

### review_code
- **Trigger**: Agent calls `review_code(task)`
- **Graph**: `reviewer → tools/format`, tool-use loop + format node
- **Tools**: `run_command`, `read_file`, `list_files` (inside E2B sandbox)
- **Output**: `SandboxReport` JSON + inline PR review comments
- **Lifecycle**: Sandbox created on entry, killed in `finally` block

## Observability

- Langfuse `CallbackHandler` attached if keys configured
- `run_name`: `grade-pr-{repo_name}-{pr_number}`
- `metadata`: repo, pr_number, sender, branch
