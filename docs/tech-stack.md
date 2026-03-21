# Tech Stack

| Слой | Технология |
|---|---|
| Язык | Python 3.13 |
| Агентная оркестрация | LangGraph |
| LLM | GLM-4.7 (Z.AI API, OpenAI-compatible) |
| LLM observability | Langfuse |
| Sandbox | E2B (Firecracker microVM) |
| GitHub App | gidgethub + httpx |
| Google Sheets | aiogoogle |
| Очередь задач | Taskiq + Redis |
| ASGI-сервер | Granian |
| HTTP-клиент | httpx |
| Конфиг | python-dotenv |
| Деплой | VPS + Docker |

## Кеширование и rate limits

| Данные | TTL кеша | Причина |
|---|---|---|
| Google Sheets (roster, deadlines, rubrics) | 1 час | Rate limit Sheets API |
| Спецификации сайта | 6 часов | Меняются редко |
| Результаты (results) | Без кеша | Пишем сразу |

## Scope PoC

**В scope:**
- Lab 1: проверка D1–D4 (структура + содержание)
- Lab 2: проверка артефактов по роли
- Lab 4: + Sandbox Agent (E2B)
- Штрафы за дедлайн
- Комментарий в PR
- Запись результатов в Sheets
- Эскалация к преподавателю

**Out of scope:**
- Plagiarism detection
- Интеграция с LMS (Moodle и др.)
- Оценка бизнес-смысла идеи
- Merge PR
- Lab 3 (определить отдельно)
- Лидерборд (вторая итерация)
