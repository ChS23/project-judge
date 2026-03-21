import httpx
from langchain_core.tools import tool

from judge.settings import settings


@tool
async def fetch_spec(lab_id: int) -> dict:
    """Получить спецификацию лабораторной работы с сайта курса.

    Args:
        lab_id: Номер лабораторной работы (1-5)
    """
    url = f"{settings.spec_base_url}/lab{lab_id}"

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(url)
        resp.raise_for_status()

    # TODO: парсинг HTML → DoD критерии + ожидаемые файлы
    return {
        "lab_id": lab_id,
        "url": url,
        "raw_html": resp.text[:5000],
        "expected_files": [],
        "dod_criteria": [],
    }
