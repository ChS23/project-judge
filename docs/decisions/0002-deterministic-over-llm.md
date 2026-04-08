# ADR-0002: Deterministic tools где возможно, LLM только для контента

**Status:** Accepted  
**Date:** 2026-03-20

## Context

LLM вызовы дорогие, медленные и недетерминированные. Часть проверок (наличие файлов, дедлайны, DoD чеклист) имеет объективный ответ и не требует LLM.

## Decision

Разделить tools на три категории:
- **Deterministic** (regex, формулы): check_artifacts, parse_dod, check_deadline, read_roster, fetch_spec, read_file, read_past_reviews
- **Sub-agent** (LLM): evaluate_content, review_code
- **Write** (side effects): post_comment, escalate, write_results

LLM используется только для оценки качества контента и code review.

## Consequences

**Positive:**
- Deterministic tools: быстрые, бесплатные, 100% воспроизводимые
- Меньше LLM вызовов = ниже стоимость и latency
- Ошибки в deterministic tools легко дебажить

**Negative:**
- Некоторые проверки (например, релевантность файла) могли бы быть точнее с LLM
- Regex-парсинг HTML spec fragile — зависит от разметки сайта

**Model/Prompt Impact:**
- System prompt инструктирует агента вызывать deterministic tools первыми
- evaluate_content работает с уже pre-processed данными (sanitized text)
