from dataclasses import dataclass, field

from judge.models.pr import PRContext


@dataclass
class GroundTruth:
    """Ожидаемые результаты для сценария."""

    expected_score_range: tuple[float, float]  # (min, max) допустимый итоговый балл
    must_find_issues: list[str] = field(
        default_factory=list
    )  # проблемы, которые агент ДОЛЖЕН найти
    must_not_miss: list[str] = field(default_factory=list)  # что обязательно в отчёте
    should_escalate: bool = False
    injection_present: bool = False
    injection_should_be_flagged: bool = False
    expected_artifacts_missing: list[str] = field(default_factory=list)
    min_criteria_covered: int = 3  # минимум критериев, которые должны быть оценены
    should_call_review_code: bool = False  # ожидаем вызов sandbox


@dataclass
class EvalScenario:
    """Один eval-сценарий = один симулированный PR."""

    name: str
    description: str
    pr_context: PRContext
    files: dict[str, str]  # path → content (симулирует репо)
    roster_entry: dict | None  # что вернёт read_roster
    rubrics: list[dict]  # что вернёт read_rubrics
    deadline: str | None  # ISO дедлайн
    spec_html: str  # HTML спецификации лабы для fetch_spec
    ground_truth: GroundTruth
    past_reviews: list[dict] = field(default_factory=list)
    sandbox_report: dict | None = (
        None  # canned SandboxReport для мока (None = не мокать)
    )
    uses_sandbox: bool = False  # помечает сценарий как sandbox
