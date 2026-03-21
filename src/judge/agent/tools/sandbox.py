from langchain_core.tools import tool

from judge.settings import settings


@tool
async def run_sandbox(repo_url: str, branch: str, demo_urls: str = "") -> dict:
    """Запустить код студента в изолированном E2B sandbox.

    Клонирует репо, запускает docker-compose, проверяет health checks и тесты.

    Args:
        repo_url: URL репозитория для клонирования
        branch: Ветка PR
        demo_urls: URLs для проверки через запятую (опционально)
    """
    if not settings.e2b_api_key:
        return {"error": "E2B API key not configured", "skipped": True}

    try:
        from e2b import Sandbox
    except ImportError:
        return {"error": "e2b package not installed", "skipped": True}

    sandbox = Sandbox(api_key=settings.e2b_api_key, timeout=settings.sandbox_timeout)

    try:
        # Clone repo
        clone_result = sandbox.commands.run(
            f"git clone --branch {branch} --single-branch {repo_url} /app"
        )
        if clone_result.exit_code != 0:
            return {
                "build": "fail",
                "stage": "clone",
                "error": clone_result.stderr,
            }

        # Docker compose up
        compose_result = sandbox.commands.run(
            "cd /app && docker-compose up -d --build",
            timeout=300,
        )
        if compose_result.exit_code != 0:
            return {
                "build": "fail",
                "stage": "docker-compose",
                "error": compose_result.stderr,
            }

        # Health check
        import httpx

        demo_alive = {}
        if demo_urls:
            for url in demo_urls.split(","):
                url = url.strip()
                alive = False
                for _attempt in range(3):
                    try:
                        async with httpx.AsyncClient(timeout=10) as client:
                            resp = await client.get(url)
                            if resp.status_code < 500:
                                alive = True
                                break
                    except httpx.RequestError:
                        import asyncio

                        await asyncio.sleep(30)
                demo_alive[url] = alive

        # Run tests
        test_result = sandbox.commands.run(
            "cd /app && pytest --tb=short -q 2>&1 || true",
            timeout=120,
        )

        return {
            "build": "pass",
            "tests_output": test_result.stdout[:3000],
            "tests_exit_code": test_result.exit_code,
            "demo_alive": demo_alive,
        }

    finally:
        sandbox.kill()
