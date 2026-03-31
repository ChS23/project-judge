from judge.github.helpers import parse_branch


def test_parse_branch_lab2_with_role():
    result = parse_branch("lab2-mlops-deliverables")
    assert result == {"lab_id": 2, "role": "mlops"}


def test_parse_branch_lab3_fullstack():
    result = parse_branch("lab3-fullstack-deliverables")
    assert result == {"lab_id": 3, "role": "fullstack"}


def test_parse_branch_lab1_arbitrary():
    result = parse_branch("lab1-team-project")
    assert result == {"lab_id": 1, "role": ""}


def test_parse_branch_no_match():
    result = parse_branch("feature/some-branch")
    assert result == {"lab_id": 0, "role": ""}


def test_parse_branch_case_insensitive():
    result = parse_branch("Lab2-PM-Deliverables")
    assert result == {"lab_id": 2, "role": "PM"}
