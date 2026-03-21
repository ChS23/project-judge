from judge.agent.tools.deadline import check_deadline


def test_on_time():
    result = check_deadline.invoke(
        {"pr_created_at": "2026-03-15T10:00:00", "deadline": "2026-03-20T23:59:00"}
    )
    assert result["coefficient"] == 1.0
    assert result["on_time"] is True
    assert result["days_late"] == 0


def test_one_day_late():
    result = check_deadline.invoke(
        {"pr_created_at": "2026-03-22T10:00:00", "deadline": "2026-03-20T23:59:00"}
    )
    assert result["coefficient"] == 0.9
    assert result["days_late"] == 1


def test_three_days_late():
    result = check_deadline.invoke(
        {"pr_created_at": "2026-03-23T10:00:00", "deadline": "2026-03-20T10:00:00"}
    )
    assert result["coefficient"] == 0.7
    assert result["days_late"] == 3


def test_week_late():
    result = check_deadline.invoke(
        {"pr_created_at": "2026-03-27T10:00:00", "deadline": "2026-03-20T10:00:00"}
    )
    assert result["coefficient"] == 0.5


def test_very_late():
    result = check_deadline.invoke(
        {"pr_created_at": "2026-04-10T10:00:00", "deadline": "2026-03-20T10:00:00"}
    )
    assert result["coefficient"] == 0.2
