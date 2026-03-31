import re

import httpx
from langchain_core.tools import tool

from judge.settings import settings

SPEC_BASE = "https://sii.sergeivolchkov.ru/materials/labs"


@tool
async def fetch_spec(lab_id: int, role: str = "") -> dict:
    """Получить спецификацию лабораторной работы с сайта курса.
    Возвращает deliverables, ожидаемые файлы и DoD критерии.
    Для lab2+ фильтрует по роли если указана.

    Args:
        lab_id: Номер лабораторной работы (1-5)
        role: Роль студента (SA/PO, Fullstack, MLOps, AI Engineer). Пусто = все роли
    """
    base = settings.spec_base_url or SPEC_BASE
    url = f"{base}/lab{lab_id}-artifacts"

    try:
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            resp = await client.get(url)
            resp.raise_for_status()
    except httpx.HTTPError as e:
        return {"lab_id": lab_id, "url": url, "error": str(e)}

    html = resp.text
    deliverables = _parse_deliverables(html)
    expected_files = _parse_expected_files(html)
    dod_criteria = _parse_dod(html)

    # Фильтрация по роли если указана
    if role:
        role_lower = role.lower()
        deliverables = [
            d
            for d in deliverables
            if not d.get("role") or role_lower in d["role"].lower()
        ]
        # Файлы привязаны к deliverables — фильтруем если можем
        if deliverables:
            d_ids = {d["id"] for d in deliverables}
            expected_files = [
                f
                for f in expected_files
                if any(d_id.lower() in f.lower() for d_id in d_ids) or "/" not in f
            ]

    return {
        "lab_id": lab_id,
        "url": url,
        "role_filter": role or "all",
        "deliverables": deliverables,
        "expected_files": expected_files,
        "dod_criteria": dod_criteria,
        "raw_text": _html_to_text(html)[:8000],
    }


def _html_to_text(html: str) -> str:
    """Грубое извлечение текста из HTML."""
    text = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL)
    text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL)
    text = re.sub(r"<[^>]+>", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


ROLE_PATTERNS = [
    (re.compile(r"SA/?PO|System\s*Architect|Product\s*Owner", re.I), "SA/PO"),
    (re.compile(r"Fullstack|Full[\s-]?stack", re.I), "Fullstack"),
    (re.compile(r"MLOps|DevOps", re.I), "MLOps"),
    (re.compile(r"AI\s*Engineer|Data\s*Scientist", re.I), "AI Engineer"),
]


def _parse_deliverables(html: str) -> list[dict]:
    """Извлечь deliverables (D1, D2, ...) с привязкой к роли."""
    deliverables = []
    text = _html_to_text(html)

    # Ищем паттерны типа "D1 — название" или "D1:" или "D1."
    pattern = re.compile(r"(D\d+)\s*[—\-:\.]\s*(.{3,80})")
    seen = set()
    current_role = ""

    for line in text.split("\n"):
        # Обновляем текущую роль если встречаем
        for rp, role_name in ROLE_PATTERNS:
            if rp.search(line):
                current_role = role_name
                break

        for match in pattern.finditer(line):
            d_id = match.group(1).upper()
            name = match.group(2).strip().rstrip(".")
            if d_id not in seen:
                seen.add(d_id)
                deliverables.append(
                    {
                        "id": d_id,
                        "name": name,
                        "role": current_role,
                    }
                )

    return deliverables


def _parse_expected_files(html: str) -> list[str]:
    """Извлечь ожидаемые пути файлов из HTML."""
    files = []

    # Паттерны файлов: docs/something.md, README.md, etc.
    file_patterns = [
        re.compile(r"[>`\"](\w[\w\-/]*\.(?:md|yml|yaml|sql|py|json|figma))[<`\"]"),
        re.compile(
            r"[>`\"]((?:docs|api|database|ml|monitoring|design|\.github)/[\w\-/.]+)[<`\"]"
        ),
        re.compile(r"[>`\"](README\.md)[<`\"]"),
        re.compile(r"[>`\"](docker-compose[\w\-]*\.ya?ml)[<`\"]"),
    ]

    seen = set()
    for pattern in file_patterns:
        for match in pattern.finditer(html):
            path = match.group(1)
            if path not in seen:
                seen.add(path)
                files.append(path)

    return sorted(files)


def _parse_dod(html: str) -> list[str]:
    """Извлечь DoD критерии из HTML."""
    criteria = []

    # Ищем чеклисты: "- [ ]" или элементы списка после "DoD" / "Definition of Done"
    text = _html_to_text(html)

    # Ищем строки после "DoD" или "Definition of Done" или "Чеклист"
    dod_section = False
    for line in text.split("\n"):
        line = line.strip()
        if re.search(r"(?:DoD|Definition of Done|[Чч]еклист)", line, re.IGNORECASE):
            dod_section = True
            continue
        if dod_section and line.startswith(("- ", "• ", "✅", "☑")):
            criterion = re.sub(r"^[-•✅☑\[\]x\s]+", "", line).strip()
            if criterion and len(criterion) > 5:
                criteria.append(criterion)
        elif dod_section and line and not line.startswith((" ", "\t", "-", "•")):
            if len(criteria) > 0:
                dod_section = False

    return criteria
