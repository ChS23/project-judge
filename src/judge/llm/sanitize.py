import re

# Паттерны prompt injection
INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?previous\s+instructions", re.IGNORECASE),
    re.compile(r"ignore\s+(all\s+)?above", re.IGNORECASE),
    re.compile(r"игнорируй\s+(все\s+)?предыдущие", re.IGNORECASE),
    re.compile(r"забудь\s+(все\s+)?инструкции", re.IGNORECASE),
    re.compile(r"ты\s+теперь\s+(?!студент)", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+a", re.IGNORECASE),
    re.compile(r"new\s+instructions?\s*:", re.IGNORECASE),
    re.compile(r"system\s*:\s*", re.IGNORECASE),
    re.compile(r"поставь\s+(?:мне\s+)?(?:10|максимум|полный\s+балл)", re.IGNORECASE),
    re.compile(
        r"give\s+(?:me\s+)?(?:full|maximum|perfect)\s+(?:score|marks|grade)",
        re.IGNORECASE,
    ),
    re.compile(r"override\s+(?:the\s+)?(?:score|grade|evaluation)", re.IGNORECASE),
    re.compile(r"<\s*/?system\s*>", re.IGNORECASE),
    re.compile(r"\[INST\]|\[/INST\]", re.IGNORECASE),
    re.compile(r"###\s*(?:system|instruction|human|assistant)\s*:", re.IGNORECASE),
]


def detect_injection(text: str) -> list[str]:
    """Проверить текст на паттерны prompt injection.

    Returns:
        Список найденных паттернов (пустой если чисто).
    """
    found = []
    for pattern in INJECTION_PATTERNS:
        matches = pattern.findall(text)
        if matches:
            found.append(f"{pattern.pattern}: {matches[:3]}")
    return found


def sanitize_content(text: str, max_length: int = 15000) -> str:
    """Очистить пользовательский контент перед передачей в LLM.

    - Обрезает до max_length
    - Удаляет null bytes
    - Оборачивает в разделители для structural isolation
    """
    text = text[:max_length]
    text = text.replace("\x00", "")
    return f"--- BEGIN STUDENT DOCUMENT ---\n{text}\n--- END STUDENT DOCUMENT ---"
