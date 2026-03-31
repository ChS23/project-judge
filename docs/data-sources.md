# Источники данных

| Данные | Где | Кто управляет |
|---|---|---|
| Спецификации артефактов, DoD чеклисты | Сайт курса (Next.js) | Преподаватель |
| Регистрация и команды | Google Sheets | Студенты |
| Конфиг курса (дедлайны, рубрики) | Google Sheets | Преподаватель |
| Результаты проверок | Google Sheets | Агент (пишет) |

## Процесс регистрации

1. Студент заполняет строку в `students` (ФИО, GitHub username, группа)
2. Студент регистрируется в GitHub Classroom → создаёт/вступает в команду
3. В `teams` выбирает себя (выпадающий из `students`), роль (выпадающий), тему (выпадающий из `topics` или своя)

## Google Sheets

### Заполняют студенты

**`students`** — саморегистрация студентов
```
full_name | github_username | group_id
```

**`teams`** — формирование команд
```
team_name | github_username | role | topic
```
- `github_username` — выпадающий из `students`
- `role` — выпадающий: SA/PO, AI Engineer, MLOps, Fullstack
- `topic` — выпадающий из `topics` или вписывается вручную
- Одна строка на участника

**`topics`** — каталог тем
```
topic_id | title | description | is_taken
```
- Готовые темы от преподавателя + свободные слоты для своих
- `is_taken` — автоформула `=COUNTIF(teams!D:D, A2) > 0`

### Заполняет преподаватель

**`deadlines`** — дедлайны по группам
```
lab_id | group_id | due_at
```

**`rubrics`** — критерии оценки по ролям
```
lab_id | deliverable_id | role | criterion | max_score | weight
```
- В Lab 1 (командный PR) — `role = *` (общие критерии)
- В Lab 2+ — критерии по роли, агент берёт только релевантные

### Автосборка формулами

**`roster`** — сводный view для агента, никто не заполняет руками
```
github_username | full_name | group_id | team_name | role | topic
```
- Собирается QUERY/VLOOKUP из `students` + `teams`
- Агент делает один lookup по `github_username` → получает всё

### Агент пишет

**`results`** — результаты проверок
```
github_username | lab_id | deliverable_id | criterion |
score | max_score | penalty_coeff | final_score |
pr_url | comment_url | flags | checked_at
```
- Одна строка = один критерий одного deliverable
- Сводные баллы — через pivot/формулы поверх
- `flags` — `needs-review`, `injection-detected`, `sandbox-error`

## Резолв контекста агентом

```
PR открыт → github_username из PR author
    ↓
roster[github_username] → group_id, team_name, role, topic
    ↓
deadlines[lab_id + group_id] → due_at → penalty_coeff
    ↓
rubrics[lab_id + role] → список критериев для оценки
    ↓
results[github_username + lab_id] → уже проверялся? (дедупликация)
```

Один линейный pipeline, каждый шаг = один запрос к Sheets API.
