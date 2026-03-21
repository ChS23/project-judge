from judge.models.pr import PRContext


def test_from_event(sample_pr_payload):
    pr = PRContext.from_event(sample_pr_payload)
    assert pr.repo == "org/repo"
    assert pr.pr_number == 42
    assert pr.sender == "student1"
    assert pr.branch == "lab2-mlops-deliverables"
    assert pr.head_sha == "abc123"
    assert pr.installation_id == 12345
    assert "README" in pr.body
