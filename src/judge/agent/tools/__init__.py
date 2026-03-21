from judge.agent.tools.artifacts import check_artifacts
from judge.agent.tools.comment import post_comment
from judge.agent.tools.content import evaluate_content
from judge.agent.tools.deadline import check_deadline
from judge.agent.tools.dod import parse_dod
from judge.agent.tools.results import write_results
from judge.agent.tools.roster import read_roster
from judge.agent.tools.sandbox import run_sandbox
from judge.agent.tools.spec import fetch_spec

all_tools = [
    read_roster,
    fetch_spec,
    check_artifacts,
    parse_dod,
    check_deadline,
    evaluate_content,
    run_sandbox,
    post_comment,
    write_results,
]
