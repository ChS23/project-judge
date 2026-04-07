from dataclasses import dataclass, field


@dataclass
class OutputCollector:
    """Собирает side effects агента (comments, labels, results)."""

    comments: list[str] = field(default_factory=list)
    reviews: list[dict] = field(default_factory=list)
    labels: list[str] = field(default_factory=list)
    results: list[dict] = field(default_factory=list)
