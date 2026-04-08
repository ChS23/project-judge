from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode
from pydantic import BaseModel, Field

from judge.github.auth import get_installation_token
from judge.github.client import post_review
from judge.llm.client import get_llm
from judge.models.pr import PRContext
from judge.settings import settings

REVIEWER_PROMPT = """\
Ты — агент для проверки кода студенческих проектов. Работаешь внутри sandbox \
с клонированным репозиторием в /home/user/repo.

## Возможности

Используй доступные tools чтобы исследовать проект и проверить его работоспособность. \
Ты сам решаешь, какие команды выполнять и в каком порядке.

## Типичный план (адаптируй под проект)

1. Изучи структуру проекта (ls, tree, cat README, etc.)
2. Прочитай ключевые файлы: точку входа, конфиги, Dockerfile
3. Оцени качество кода (см. критерии ниже)
4. Запусти сборку
5. Запусти тесты если есть
6. Если есть docker-compose — подними сервисы и проверь health
7. Проверь логи если что-то упало

## Критерии качества кода (минимум junior-уровень)

Код должен соответствовать хотя бы базовым стандартам. Отмечай нарушения:

**Структура проекта:**
- Есть осмысленное разделение на модули/пакеты, а не всё в одном файле
- Есть .gitignore, README с инструкцией запуска
- Нет коммитов node_modules, .env, __pycache__, билд-артефактов

**Качество кода:**
- Осмысленные имена переменных и функций (не a, b, x, temp, data1)
- Функции не длиннее ~50 строк, делают одну вещь
- Нет copy-paste дублирования
- Нет захардкоженных секретов, паролей, токенов
- Есть обработка ошибок на границах системы (API, БД, файлы)
- Нет закомментированного мёртвого кода

**Архитектура:**
- Логика не в обработчиках роутов / контроллерах — есть слой сервисов или хотя бы выделенные функции
- Конфигурация через env / файлы, не захардкожена
- Зависимости явные (requirements.txt / package.json / go.mod)

**Инфраструктура (если есть Docker):**
- Dockerfile собирается без ошибок
- Используется multi-stage build или хотя бы не тянет лишнее
- docker-compose поднимает все заявленные сервисы
- Health checks работают

## Правила

- Рабочая директория: /home/user/repo
- Если команда зависла — попробуй с timeout или другой подход
- Не модифицируй код студента
- Будь конкретным: указывай файлы и строки где нашёл проблемы
- Для каждой проблемы в коде запоминай path (относительный от корня репо) и номер строки — \
они попадут в inline-комментарии к PR
"""


class InlineComment(BaseModel):
    """Inline-комментарий к конкретной строке кода."""

    path: str = Field(
        description="Относительный путь от корня репо (например: src/main.py)"
    )
    line: int = Field(description="Номер строки в файле")
    body: str = Field(description="Текст комментария")


class SandboxReport(BaseModel):
    """Структурированный отчёт суб-агента по проверке кода."""

    project_structure: str = Field(description="Краткое описание структуры проекта")
    build_status: str = Field(description="pass / fail / skipped")
    build_details: str = Field(description="Детали сборки: команда, ошибки, warnings")
    tests_status: str = Field(description="pass / fail / not_found / skipped")
    tests_output: str = Field(description="Вывод тестов (первые 3000 символов)")
    services: list[str] = Field(
        description="Список поднятых сервисов и их статус health check"
    )
    code_quality_issues: list[str] = Field(
        description="Проблемы качества кода: плохие имена, дублирование, захардкоженные секреты, мёртвый код и т.д. Формат: 'файл:строка — описание'"
    )
    architecture_issues: list[str] = Field(
        description="Проблемы архитектуры: логика в роутах, нет разделения слоёв, захардкоженный конфиг и т.д."
    )
    inline_comments: list[InlineComment] = Field(
        description="Inline-комментарии к конкретным строкам кода"
    )
    issues: list[str] = Field(
        description="Прочие проблемы: сборка, тесты, инфраструктура"
    )
    summary: str = Field(description="Общий вывод в 2-3 предложения")


def _make_sandbox_tools(sandbox):
    """Создаёт tools для работы внутри E2B sandbox."""

    @tool
    def run_command(command: str, timeout: int = 60) -> dict:
        """Выполнить shell-команду в sandbox.

        Args:
            command: Shell-команда для выполнения
            timeout: Таймаут в секундах (по умолчанию 60)
        """
        result = sandbox.commands.run(command, timeout=timeout)
        return {
            "exit_code": result.exit_code,
            "stdout": result.stdout[:5000],
            "stderr": result.stderr[:3000],
        }

    @tool
    def read_file(path: str) -> str:
        """Прочитать файл в sandbox.

        Args:
            path: Абсолютный путь к файлу
        """
        try:
            content = sandbox.files.read(path)
            return content[:10000]
        except Exception as e:
            return f"Error reading {path}: {e}"

    @tool
    def list_files(path: str = "/home/user/repo") -> str:
        """Показать содержимое директории в sandbox.

        Args:
            path: Путь к директории
        """
        import shlex

        result = sandbox.commands.run(
            f"find {shlex.quote(path)} -maxdepth 3 -not -path '*/node_modules/*' -not -path '*/.git/*' | head -100"
        )
        return result.stdout[:5000]

    return [run_command, read_file, list_files]


def _build_code_reviewer(sandbox):
    """Собирает tool-use loop агент для code review внутри sandbox."""
    tools = _make_sandbox_tools(sandbox)
    llm = get_llm()
    tool_llm = llm.bind_tools(tools)
    format_llm = llm.with_structured_output(SandboxReport)

    async def agent_node(state: MessagesState) -> dict:
        messages = [SystemMessage(content=REVIEWER_PROMPT), *state["messages"]]
        response = await tool_llm.ainvoke(messages)
        return {"messages": [response]}

    async def format_node(state: MessagesState) -> dict:
        messages = [
            SystemMessage(
                content="Сформируй структурированный отчёт на основе всей собранной информации."
            ),
            *state["messages"],
        ]
        report = await format_llm.ainvoke(messages)
        return {"messages": [HumanMessage(content=report.model_dump_json())]}

    def should_continue(state: MessagesState) -> str:
        last = state["messages"][-1]
        if hasattr(last, "tool_calls") and last.tool_calls:
            return "tools"
        return "format"

    graph = StateGraph(MessagesState)
    graph.add_node("reviewer", agent_node)
    graph.add_node("tools", ToolNode(tools))
    graph.add_node("format", format_node)
    graph.add_edge(START, "reviewer")
    graph.add_conditional_edges(
        "reviewer",
        should_continue,
        {
            "tools": "tools",
            "format": "format",
        },
    )
    graph.add_edge("tools", "reviewer")
    graph.add_edge("format", END)

    return graph.compile()


def make_review_code(pr: PRContext):
    @tool
    async def review_code(task: str) -> str:
        """Запустить суб-агент для проверки кода в изолированном sandbox.

        Суб-агент клонирует репозиторий студента и самостоятельно исследует проект: \
        изучает структуру, запускает сборку, тесты, поднимает сервисы. \
        Вызывай ТОЛЬКО если лаба требует проверки работоспособности кода.

        Args:
            task: Что конкретно нужно проверить (например: "Проверь что docker-compose поднимает все сервисы и тесты проходят")
        """
        if not settings.e2b_api_key:
            return "E2B sandbox не настроен — пропускаю проверку кода."

        try:
            from e2b import Sandbox
        except ImportError:
            return "e2b пакет не установлен — пропускаю проверку кода."

        token = await get_installation_token(pr.installation_id)
        repo_url = f"https://github.com/{pr.repo}.git"

        sandbox = Sandbox(
            api_key=settings.e2b_api_key, timeout=settings.sandbox_timeout
        )

        try:
            try:
                sandbox.git.clone(
                    repo_url,
                    path="/home/user/repo",
                    branch=pr.branch,
                    depth=1,
                    username="x-access-token",
                    password=token,
                )
            except Exception as e:
                return f"Не удалось клонировать репозиторий: {e}"

            reviewer = _build_code_reviewer(sandbox)
            result = await reviewer.ainvoke(
                {"messages": [HumanMessage(content=task)]},
            )

            raw = result["messages"][-1].content

            try:
                report = SandboxReport.model_validate_json(raw)
            except Exception:
                return raw

            if report.inline_comments:
                await post_review(
                    pr,
                    body=f"🤖 **Code Review — автопроверка**\n\n{report.summary}",
                    comments=[
                        {
                            "path": c.path,
                            "line": c.line,
                            "body": c.body,
                        }
                        for c in report.inline_comments
                    ],
                )

            return report.model_dump_json()

        finally:
            sandbox.kill()

    return review_code
