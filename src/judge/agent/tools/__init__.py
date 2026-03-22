from judge.agent.tools.artifacts import make_check_artifacts
from judge.agent.tools.comment import make_escalate, make_post_comment
from judge.agent.tools.content import evaluate_content
from judge.agent.tools.deadline import check_deadline
from judge.agent.tools.dod import parse_dod
from judge.agent.tools.results import make_write_results
from judge.agent.tools.roster import make_read_roster
from judge.agent.tools.sandbox import make_review_code
from judge.agent.tools.spec import fetch_spec
from judge.models.pr import PRContext


def get_all_tools(pr: PRContext):
    return [
        make_read_roster(pr),
        fetch_spec,
        make_check_artifacts(pr),
        parse_dod,
        check_deadline,
        evaluate_content,
        make_review_code(pr),
        make_post_comment(pr),
        make_escalate(pr),
        make_write_results(pr),
    ]
