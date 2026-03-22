from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool
from langgraph.graph import START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from judge.github.auth import get_installation_token
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
2. Найди конфигурацию сборки (Dockerfile, docker-compose.yml, Makefile, package.json, etc.)
3. Запусти сборку
4. Запусти тесты если есть
5. Если есть docker-compose — подними сервисы и проверь health
6. Проверь логи если что-то упало

## Правила

- Рабочая директория: /home/user/repo
- Если команда зависла — попробуй с timeout или другой подход
- Не модифицируй код студента
- Верни структурированный отчёт о результатах

## Формат ответа

В конце верни отчёт:
- **Структура проекта:** краткое описание
- **Сборка:** pass/fail + детали
- **Тесты:** pass/fail/not found + вывод
- **Сервисы:** какие поднялись, health check результаты
- **Проблемы:** что не работает и почему
"""


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
        result = sandbox.commands.run(
            f"find {path} -maxdepth 3 -not -path '*/node_modules/*' -not -path '*/.git/*' | head -100"
        )
        return result.stdout[:5000]

    return [run_command, read_file, list_files]


def _build_code_reviewer(sandbox):
    """Собирает tool-use loop агент для code review внутри sandbox."""
    tools = _make_sandbox_tools(sandbox)
    llm = get_llm()
    llm_with_tools = llm.bind_tools(tools)

    async def agent_node(state: MessagesState) -> dict:
        messages = [SystemMessage(content=REVIEWER_PROMPT), *state["messages"]]
        response = await llm_with_tools.ainvoke(messages)
        return {"messages": [response]}

    graph = StateGraph(MessagesState)
    graph.add_node("reviewer", agent_node)
    graph.add_node("tools", ToolNode(tools))
    graph.add_edge(START, "reviewer")
    graph.add_conditional_edges("reviewer", tools_condition)
    graph.add_edge("tools", "reviewer")

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
            sandbox.git.clone(
                repo_url,
                path="/home/user/repo",
                branch=pr.branch,
                depth=1,
                username="x-access-token",
                password=token,
            )

            reviewer = _build_code_reviewer(sandbox)
            result = await reviewer.ainvoke(
                {"messages": [HumanMessage(content=task)]},
            )
            return result["messages"][-1].content

        finally:
            sandbox.kill()

    return review_code
