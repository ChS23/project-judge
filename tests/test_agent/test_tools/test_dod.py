from judge.agent.tools.dod import parse_dod


def test_mixed_checklist():
    body = "- [x] README\n- [ ] Architecture\n- [x] Tests\n- [ ] Demo"
    result = parse_dod.invoke({"pr_body": body})
    assert result["checked"] == 2
    assert result["unchecked"] == 2
    assert result["total"] == 4
    assert result["completion_rate"] == 0.5


def test_all_checked():
    body = "- [x] A\n- [x] B\n- [x] C"
    result = parse_dod.invoke({"pr_body": body})
    assert result["checked"] == 3
    assert result["completion_rate"] == 1.0


def test_empty_body():
    result = parse_dod.invoke({"pr_body": ""})
    assert result["total"] == 0
    assert result["completion_rate"] == 0.0


def test_no_checklist():
    result = parse_dod.invoke({"pr_body": "Just some text without checkboxes"})
    assert result["total"] == 0
