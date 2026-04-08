"""Standalone eval runner с таблицей результатов."""

import asyncio
import time
from datetime import UTC, datetime
from pathlib import Path

from langchain_core.messages import HumanMessage

from judge.agent.graph import build_agent
from tests.test_eval.judge.llm_judge import judge_report
from tests.test_eval.judge.models import AggregateMetrics, EvalReport, ScenarioResult
from tests.test_eval.scenarios.bad_code import bad_code_scenario
from tests.test_eval.scenarios.empty_docs import empty_docs_scenario
from tests.test_eval.scenarios.injection_attempt import injection_attempt_scenario
from tests.test_eval.scenarios.partial_completion import partial_completion_scenario
from tests.test_eval.scenarios.perfect_work import perfect_work_scenario

ALL_SCENARIOS = [
    perfect_work_scenario(),
    empty_docs_scenario(),
    injection_attempt_scenario(),
    partial_completion_scenario(),
    bad_code_scenario(),
]


async def run_single(scenario) -> ScenarioResult:
    """Запустить агента и оценить через LLM-as-judge."""
    # Mocks are applied by the caller
    agent = build_agent(scenario.pr_context)
    start = time.time()
    result = await agent.ainvoke(
        {
            "messages": [
                HumanMessage(content=f"Проверь PR #{scenario.pr_context.pr_number}")
            ]
        },
        config={"recursion_limit": 30},
    )
    duration = time.time() - start
    report = str(result["messages"][-1].content)

    verdict = await judge_report(report, scenario)

    return ScenarioResult(
        scenario_name=scenario.name,
        agent_report=report[:2000],
        judge_verdict=verdict,
        duration_seconds=duration,
        passed=verdict.verdict != "POOR",
    )


def print_table(results: list[ScenarioResult]):
    """Печатает таблицу результатов."""
    header = f"{'Scenario':<25} {'Verdict':<10} {'C1':>4} {'C2':>4} {'C3':>4} {'C4':>4} {'C5':>4} {'Total':>7} {'Time':>6}"
    sep = "-" * len(header)

    print(f"\n{sep}")
    print(header)
    print(sep)

    for r in results:
        v = r.judge_verdict
        status = "PASS" if r.passed else "FAIL"
        print(
            f"{r.scenario_name:<25} "
            f"{v.verdict:<10} "
            f"{v.c1_rubric_coverage.score:>4} "
            f"{v.c2_comment_specificity.score:>4} "
            f"{v.c3_problem_detection.score:>4} "
            f"{v.c4_injection_resistance.score:>4} "
            f"{v.c5_score_reasonableness.score:>4} "
            f"{v.weighted_total:>7.2f} "
            f"{r.duration_seconds:>5.0f}s"
        )

    print(sep)

    passed = sum(1 for r in results if r.passed)
    total = len(results)
    avg_score = (
        sum(r.judge_verdict.weighted_total for r in results) / total if total else 0
    )
    total_time = sum(r.duration_seconds for r in results)

    print(
        f"{'TOTAL':<25} {passed}/{total:<8} {'':>4} {'':>4} {'':>4} {'':>4} {'':>4} {avg_score:>7.2f} {total_time:>5.0f}s"
    )
    print(sep)


async def main():
    from contextlib import ExitStack
    from unittest.mock import AsyncMock, MagicMock, patch

    from tests.test_eval.mocks import OutputCollector
    from tests.test_eval.mocks.github_mock import make_github_mocks
    from tests.test_eval.mocks.sandbox_mock import make_sandbox_mock
    from tests.test_eval.mocks.sheets_mock import make_sheets_mocks

    results = []

    for scenario in ALL_SCENARIOS:
        print(f"\nRunning: {scenario.name}...")
        collector = OutputCollector()

        github_mocks = make_github_mocks(scenario, collector)
        sheets_mocks = make_sheets_mocks(scenario, collector)
        sandbox_mocks = make_sandbox_mock(scenario)

        # Spec mock
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = scenario.spec_html
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        all_mocks = {
            **github_mocks,
            **sheets_mocks,
            **sandbox_mocks,
            "judge.agent.tools.spec.httpx.AsyncClient": lambda *a, **kw: mock_client,
        }

        with ExitStack() as stack:
            for target, mock_fn in all_mocks.items():
                stack.enter_context(patch(target, side_effect=mock_fn))

            try:
                result = await run_single(scenario)
                results.append(result)
                status = "PASS" if result.passed else "FAIL"
                print(
                    f"  {status}: {result.judge_verdict.verdict} ({result.judge_verdict.weighted_total:.2f})"
                )
            except Exception as e:
                print(f"  ERROR: {e}")

    print_table(results)

    # Save report
    if results:
        passed = sum(1 for r in results if r.passed)
        total = len(results)
        scores = [r.judge_verdict for r in results]

        report = EvalReport(
            timestamp=datetime.now(UTC).isoformat(),
            scenarios=results,
            aggregate=AggregateMetrics(
                total_scenarios=total,
                passed=passed,
                failed=total - passed,
                pass_rate=passed / total,
                avg_weighted_score=sum(s.weighted_total for s in scores) / total,
                avg_c1=sum(s.c1_rubric_coverage.score for s in scores) / total,
                avg_c2=sum(s.c2_comment_specificity.score for s in scores) / total,
                avg_c3=sum(s.c3_problem_detection.score for s in scores) / total,
                avg_c4=sum(s.c4_injection_resistance.score for s in scores) / total,
                avg_c5=sum(s.c5_score_reasonableness.score for s in scores) / total,
                worst_scenario=min(
                    results, key=lambda r: r.judge_verdict.weighted_total
                ).scenario_name,
                total_duration_seconds=sum(r.duration_seconds for r in results),
            ),
        )

        reports_dir = Path("tests/test_eval/reports")
        reports_dir.mkdir(exist_ok=True)
        ts = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        report_path = reports_dir / f"eval_{ts}.json"
        report_path.write_text(report.model_dump_json(indent=2))
        print(f"\nReport saved: {report_path}")


if __name__ == "__main__":
    asyncio.run(main())
