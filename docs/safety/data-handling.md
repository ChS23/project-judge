# Data Handling Policy

## Какие данные обрабатываются

| Data | Source | Contains PII? | Sent to LLM? | Stored? |
|------|--------|--------------|---------------|---------|
| GitHub username | Webhook | Pseudonymous | Yes (in prompt) | Sheets, logs |
| PR body (description) | Webhook | Unlikely | Yes (truncated 2000 chars) | No |
| File content | GitHub API | Possible | Yes (truncated 10-15K chars) | No |
| PR created_at | Webhook | No | Yes | Sheets |
| Branch name | Webhook | No | Yes | Logs |
| ФИО студента | Google Sheets | **Yes** | No (only in write_results) | Sheets |
| Группа, команда, роль | Google Sheets | No | Yes (in context) | Sheets |
| Оценки (scores) | Agent output | No | No (after generation) | Sheets, PR comment |
| Sandbox output | E2B | No | Yes (truncated) | No |

## Что отправляется в Z.AI (LLM)

- System prompt (фиксированный, не содержит PII)
- GitHub username (pseudonymous)
- Содержимое файлов студента (truncated)
- Рубрики и критерии (из Sheets)
- PR metadata (branch, body, created_at)

**НЕ отправляется:** ФИО, email, номер группы (если не в файлах студента).

## Что отправляется в E2B (Sandbox)

- Код студента (через git clone)
- GitHub installation token (временный, 50 min TTL)

Sandbox изолирован (Firecracker microVM), данные удаляются при `sandbox.kill()`.

## Что отправляется в Langfuse (Tracing)

- LLM промпты и ответы (могут содержать username и файлы студента)
- Tool call аргументы и результаты
- Метаданные: repo, pr_number, sender, branch

**Retention:** определяется Langfuse plan (cloud: 30 days по умолчанию).

## Logging Policy

- **structlog** логирует: events (grading_start, grading_done, error), PR metadata
- **НЕ логируется:** полный текст файлов, оценки, содержимое комментариев
- Sandbox output truncated в tool results (5000/3000 chars)

## Google Sheets

- **roster:** ФИО, GitHub username, группа, команда, роль
- **results:** username, lab_id, scores, timestamps
- **leaderboard:** команда, суммарные баллы (без ФИО)

Доступ: service account + sharing permissions на spreadsheet.
