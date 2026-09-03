from data_quality.coverage_validator import (
    CoverageRule,
    validate_coverage_rule,
)


RULE = CoverageRule(
    name="execution_has_exactly_one_test",
    source_dataset="executions",
    source_column="id",
    relationship_dataset="execution_of",
    relationship_column="executionId",
    minimum_matches=1,
    maximum_matches=1,
)


def test_accepts_exactly_one_relationship():
    rows = {
        "executions": [
            {"id": "EXEC-001"},
        ],
        "execution_of": [
            {
                "executionId": "EXEC-001",
                "testId": "TEST-001",
            },
        ],
    }

    assert validate_coverage_rule(RULE, rows) == []


def test_detects_missing_relationship():
    rows = {
        "executions": [
            {"id": "EXEC-001"},
        ],
        "execution_of": [],
    }

    issues = validate_coverage_rule(RULE, rows)

    assert any("minimum is 1" in issue for issue in issues)


def test_detects_too_many_relationships():
    rows = {
        "executions": [
            {"id": "EXEC-001"},
        ],
        "execution_of": [
            {
                "executionId": "EXEC-001",
                "testId": "TEST-001",
            },
            {
                "executionId": "EXEC-001",
                "testId": "TEST-002",
            },
        ],
    }

    issues = validate_coverage_rule(RULE, rows)

    assert any("maximum is 1" in issue for issue in issues)