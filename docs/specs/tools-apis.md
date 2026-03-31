# Tools & API Integrations Spec

## Tool Contracts

### Deterministic Tools

#### read_past_reviews
- **Input**: (implicit from PRContext)
- **Output**: Formatted string with past bot grading comments (each truncated to 3000 chars)
- **Side effects**: None (GitHub API read)
- **Errors**: GitHub API error → exception
- **Timeout**: 30s
- **Notes**: Returns "Прошлых оценок нет" on first check. Matches comments by `[bot]` suffix + "Результат" keyword.

#### read_roster
- **Input**: (implicit from PRContext: repo, sender)
- **Output**: `{github_username, full_name, group_id, team_name, role, topic}` | `{error}`
- **Side effects**: None (cached read)
- **Errors**: Sheets unavailable → `{error: "..."}`
- **Timeout**: 30s (httpx default)

#### fetch_spec
- **Input**: `lab_id: int, role: str = ""`
- **Output**: `{deliverables: [...], expected_files: [...], dod_criteria: [...], raw_text: str}`
- **Side effects**: None
- **Errors**: HTTP 404 → `{error: "spec not found"}`
- **Timeout**: 30s
- **Notes**: HTML parsed with regex, not DOM parser; fragile to markup changes

#### check_artifacts
- **Input**: `expected_files: list[str]`
- **Output**: `{present: [...], missing: [...], extra_files: [...], total_expected, total_found}`
- **Side effects**: None (GitHub API read)
- **Errors**: GitHub API error propagated
- **Timeout**: 30s

#### read_file
- **Input**: `path: str`
- **Output**: File content (max 15000 chars) | `"File not found: {path}"`
- **Side effects**: None
- **Errors**: 404 → "File not found", other → exception string
- **Timeout**: 30s
- **Protection**: Content truncated at 15000 chars

#### parse_dod
- **Input**: `pr_body: str`
- **Output**: `{checked: int, unchecked: int, total: int, completion_rate: float}`
- **Side effects**: None
- **Errors**: No checkboxes → `{total: 0, completion_rate: 0}`
- **Timeout**: Instant (pure regex)

#### check_deadline
- **Input**: `pr_created_at: str (ISO), deadline: str (ISO)`
- **Output**: `{days_late: int, coefficient: float, on_time: bool}`
- **Side effects**: None
- **Timeout**: Instant (datetime math)

### Sub-agent Tools

#### evaluate_content
- **Input**: `document_text: str, criteria: str`
- **Output**: Markdown table with scores + injection warning if detected
- **Side effects**: LLM call (Z.AI)
- **Errors**: LLM timeout → exception propagated to agent
- **Protection**: `sanitize_content()` + `detect_injection()` before LLM call
- **Budget**: document_text truncated at 10000 chars

#### review_code
- **Input**: `task: str`
- **Output**: `SandboxReport` JSON
- **Side effects**: E2B sandbox (create + destroy), LLM calls, **posts inline PR review**
- **Errors**: E2B unavailable → skip message; parse error → raw text fallback
- **Timeout**: 600s (sandbox_timeout)
- **Protection**: `shlex.quote()`, sandbox auto-kill in `finally`

### Write Tools

#### post_comment
- **Input**: `body: str` (markdown)
- **Output**: `"Комментарий опубликован в PR #{N}"`
- **Side effects**: GitHub API POST
- **Errors**: 403/422 → exception
- **Idempotency**: None — multiple calls create multiple comments

#### escalate
- **Input**: `reason: str`
- **Output**: `"PR #{N} помечен для ручной проверки: {reason}"`
- **Side effects**: GitHub API — add label `needs-review`
- **Idempotency**: Label add is idempotent (GitHub ignores duplicates)

#### write_results
- **Input**: Grading fields (username, lab_id, scores, etc.)
- **Output**: Confirmation string
- **Side effects**: Append row to Google Sheets
- **Errors**: Sheets API error → exception
- **Idempotency**: None — multiple calls append multiple rows

#### trigger_recheck (Q&A agent only)
- **Input**: None (PRContext implicit)
- **Output**: `"Перепроверка запущена..."`
- **Side effects**: Enqueues `grade_pr` task via `grade_pr.kiq(pr)`
- **Errors**: Redis unavailable → Taskiq exception
- **Idempotency**: Multiple calls = multiple grading tasks enqueued
- **Notes**: Available only in Q&A agent, not in grading agent. Does not consume hint counter.

## External API Details

### Z.AI (GLM-4.7)

| Parameter | Value |
|-----------|-------|
| Endpoint | `https://api.z.ai/api/coding/paas/v4` |
| Auth | `Authorization: Bearer {ZAI_API_KEY}` |
| Model | `glm-4.7` |
| Temperature | 0.1 |
| Features used | Chat completions, function calling, structured output |
| Rate limits | Not publicly documented |
| Retry | LangChain built-in exponential backoff on 429 |

### GitHub REST API v3

| Parameter | Value |
|-----------|-------|
| Auth | Installation token (JWT → `/app/installations/{id}/access_tokens`) |
| Token TTL | 60 min (cached 55 min) |
| Rate limit | 5000 req/h per installation |
| Endpoints used | `/repos/{}/pulls/{}/files`, `/repos/{}/contents/{}`, `/repos/{}/issues/{}/comments`, `/repos/{}/pulls/{}/reviews`, `/repos/{}/issues/{}/labels` |

### E2B Sandbox

| Parameter | Value |
|-----------|-------|
| Auth | `E2B_API_KEY` |
| Sandbox timeout | 600s (configurable via `SANDBOX_TIMEOUT`) |
| Git clone | `sandbox.git.clone()` with installation token |
| Concurrency | 20 sandboxes (plan limit) |
| Cleanup | `sandbox.kill()` in `finally` block |

### Google Sheets (aiogoogle)

| Parameter | Value |
|-----------|-------|
| Auth | Service account JSON |
| Sheets | roster, rubrics, deadlines, results |
| Rate limit | 300 req/min |
| Caching | 300s TTL (roster, rubrics) |
| Repo-to-sheet mapping | `SPREADSHEET_MAP` JSON env var |
