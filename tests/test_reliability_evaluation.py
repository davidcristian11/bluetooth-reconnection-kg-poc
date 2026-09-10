from evaluation import EvaluationResult
from reliability_evaluation import (
    build_reliability_summary,
    normalize_cypher,
    percentage,
)


def make_result(
    case_id="EVAL-001",
    *,
    correct=True,
    attempts=1,
    retry_reason=None,
    cypher="MATCH (n) RETURN n.id",
):
    return EvaluationResult(
        case_id=case_id,
        category="entity_lookup",
        question="Example question?",
        execution_success=True,
        retrieval_correct=correct,
        answer_correct=correct,
        generation_attempts=attempts,
        retry_reason=retry_reason,
        cypher=cypher,
        records=[],
        answer="Example answer",
        retrieval_issues=[],
        answer_issues=[],
        error=None,
    )


def test_normalize_cypher_ignores_whitespace():
    first = normalize_cypher(
        "MATCH (n)\nRETURN n.id"
    )

    second = normalize_cypher(
        "MATCH (n)   RETURN n.id"
    )

    assert first == second


def test_percentage_handles_zero_denominator():
    assert percentage(1, 0) == 0.0


def test_summary_tracks_retries_and_perfect_runs():
    runs = [
        [
            make_result(
                "EVAL-001",
            ),
            make_result(
                "EVAL-002",
                attempts=2,
                retry_reason=(
                    "suspicious_empty_result"
                ),
            ),
        ],
        [
            make_result(
                "EVAL-001",
            ),
            make_result(
                "EVAL-002",
            ),
        ],
    ]

    summary = build_reliability_summary(
        runs
    )

    assert summary["total_runs"] == 2
    assert summary["total_case_executions"] == 4
    assert summary["perfect_runs"] == 2
    assert summary["fully_correct_executions"] == 4
    assert summary["executions_with_retry"] == 1
    assert summary["retry_rate"] == 25.0

    assert summary["retry_reasons"] == {
        "suspicious_empty_result": 1
    }


def test_summary_detects_cypher_variation():
    runs = [
        [
            make_result(
                cypher=(
                    "MATCH (n) RETURN n.id"
                ),
            )
        ],
        [
            make_result(
                cypher=(
                    "MATCH (n) RETURN "
                    "n.id AS id"
                ),
            )
        ],
    ]

    summary = build_reliability_summary(
        runs
    )

    assert (
        summary[
            "cases_with_cypher_variation"
        ]
        == ["EVAL-001"]
    )

    assert (
        summary["by_case"]["EVAL-001"][
            "unique_cypher_count"
        ]
        == 2
    )