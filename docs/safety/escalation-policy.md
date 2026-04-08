# Escalation Policy

## Когда агент эскалирует

Агент вызывает `escalate(reason)` → добавляет label `needs-review` к PR.

| Trigger | Threshold | Rationale |
|---------|-----------|-----------|
| Borderline score | Final score 40-60% от максимума | Неуверенная оценка, требует человеческого суждения |
| Prompt injection | Обнаружен паттерн injection | Возможная манипуляция оценкой |
| Sandbox error | review_code завершился с ошибкой | Невозможно проверить код |
| Student not in roster | Студент не найден в Google Sheets | Возможна ошибка в регистрации |

## Что делает инструктор

1. Видит label `needs-review` на PR в GitHub
2. Читает комментарий агента с причиной эскалации
3. Проверяет оценку вручную
4. Корректирует если нужно
5. Убирает label `needs-review`

## Что агент НЕ делает (irreversibility policy)

| Action | Allowed? |
|--------|----------|
| Post comment | Yes |
| Add label | Yes |
| Write to Sheets | Yes |
| **Merge PR** | **No — NEVER** |
| **Delete files** | **No — NEVER** |
| **Modify student repo** | **No — NEVER** |
| **Close PR** | **No — NEVER** |

## Recheck flow

Студент может запросить перепроверку:
1. Пишет комментарий в PR ("исправил, перепроверьте")
2. Q&A агент распознаёт намерение и вызывает `trigger_recheck`
3. Грейдинг-агент запускается заново
4. Первым шагом читает прошлые оценки (`read_past_reviews`)
5. В отчёте отмечает что исправлено, что нет
