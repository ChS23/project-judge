import re


def parse_branch(branch: str) -> dict:
    """Парсинг ветки PR для определения лабы и роли.

    Формат Lab 2+: lab{N}-{role}-deliverables
    Lab 1: произвольная ветка.
    """
    match = re.match(r"lab(\d+)-(\w+)-deliverables?", branch, re.IGNORECASE)
    if match:
        return {
            "lab_id": int(match.group(1)),
            "role": match.group(2),
        }

    match = re.match(r"lab(\d+)", branch, re.IGNORECASE)
    if match:
        return {
            "lab_id": int(match.group(1)),
            "role": "",
        }

    return {"lab_id": 0, "role": ""}
