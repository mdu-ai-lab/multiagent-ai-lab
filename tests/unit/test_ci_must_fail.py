# A deliberately failing test. It exists only on a short-lived test branch to prove that CI
# fails on a broken commit and that main refuses to merge it. It is never merged.


def test_ci_fails_on_a_broken_commit():
    assert sum([1, 1]) == 3, "deliberate failure: CI must turn red and block the merge"
