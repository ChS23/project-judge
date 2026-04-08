# ADR-0001: Tool-use loop вместо статического графа

**Status:** Accepted  
**Date:** 2026-03-20

## Context

Разные лабораторные требуют разных проверок: одни — только документы, другие — код в sandbox, третьи — и то, и другое. Статический граф (hardcoded sequence) потребовал бы отдельного пайплайна для каждого типа лабы.

## Decision

Использовать tool-use loop agent на базе LangGraph (`StateGraph` + `ToolNode` + `tools_condition`). Агент сам решает какие tools вызвать и в каком порядке.

## Consequences

**Positive:**
- Одна кодовая база для всех типов лаб
- Агент адаптируется к нестандартным ситуациям (missing files, unknown lab format)
- Легко добавлять новые tools без изменения графа

**Negative:**
- Менее предсказуемое поведение — агент может пропустить шаг
- Сложнее тестировать (trajectory не детерминированный)
- Нужен `recursion_limit` как safety net

**Mitigations:**
- Eval framework с trajectory assertions
- Report validation с auto-retry
- Подробные инструкции в system prompt (рекомендованный порядок)
