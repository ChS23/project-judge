from typing import Literal

from pydantic import BaseModel, Field


class CriterionScore(BaseModel):
    score: int = Field(ge=1, le=5)
    rationale: str


class JudgeVerdict(BaseModel):
    c1_rubric_coverage: CriterionScore
    c2_comment_specificity: CriterionScore
    c3_problem_detection: CriterionScore
    c4_injection_resistance: CriterionScore
    c5_score_reasonableness: CriterionScore
    weighted_total: float
    verdict: Literal["GOOD", "ACCEPTABLE", "POOR"]
    summary: str


class ScenarioResult(BaseModel):
    scenario_name: str
    agent_report: str
    posted_comments: list[str] = []
    posted_labels: list[str] = []
    written_results: list[dict] = []
    judge_verdict: JudgeVerdict
    duration_seconds: float
    passed: bool


class AggregateMetrics(BaseModel):
    total_scenarios: int
    passed: int
    failed: int
    pass_rate: float
    avg_weighted_score: float
    avg_c1: float
    avg_c2: float
    avg_c3: float
    avg_c4: float
    avg_c5: float
    worst_scenario: str
    total_duration_seconds: float


class EvalReport(BaseModel):
    timestamp: str
    scenarios: list[ScenarioResult]
    aggregate: AggregateMetrics
