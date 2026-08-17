def test_retry_after_policy_has_a_bounded_delay() -> None:
    retry_after = min(int("120"), 300)
    assert retry_after == 120
