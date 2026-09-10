import json

import pytest

from evaluation import (
    BenchmarkDefinitionError,
    EvaluationResult,
    build_summary,
    classify_result,
    evaluate_answer,
    evaluate_retrieval,
    load_benchmark,
    write_results,
)


def make_result(
    *,
    execution=True,
    retrieval=True,
    answer=True,
):
    return EvaluationResult(
        case_id="EVAL-001",
        category="entity_lookup",
        question="Example question?",
        execution_success=execution,
        retrieval_correct=retrieval,
        answer_correct=answer,
        generation_attempts=1,
        cypher="MATCH (n) RETURN n",
        records=[],
        answer="Example answer",
        retrieval_issues=[],
        answer_issues=[],
        error=None,
    )


def test_loads_valid_benchmark(tmp_path):
    path = tmp_path / "benchmark.yaml"

    path.write_text(
        """
version: 1
cases:
  - id: EVAL-001
    category: entity_lookup
    question: What requirement does TEST-001 verify?
    expected:
      result: non_empty
      required_values:
        - REQ-001
""",
        encoding="utf-8",
    )

    version, cases = load_benchmark(path)

    assert version == 1
    assert len(cases) == 1
    assert cases[0].id == "EVAL-001"


def test_rejects_duplicate_benchmark_ids(tmp_path):
    path = tmp_path / "benchmark.yaml"

    path.write_text(
        """
version: 1
cases:
  - id: EVAL-001
    category: entity_lookup
    question: Question one?
    expected:
      result: non_empty

  - id: EVAL-001
    category: entity_lookup
    question: Question two?
    expected:
      result: non_empty
""",
        encoding="utf-8",
    )

    with pytest.raises(
        BenchmarkDefinitionError,
        match="Duplicate benchmark case id",
    ):
        load_benchmark(path)


def test_numeric_retrieval_matches_number_inside_text():
    records = [
        {
            "message": (
                "Phone reconnected in 18.0 seconds."
            )
        }
    ]

    expected = {
        "result": "non_empty",
        "required_values": [18.0],
    }

    correct, issues = evaluate_retrieval(
        records,
        expected,
    )

    assert correct is True
    assert issues == []


def test_exact_id_set_rejects_extra_entity():
    records = [
        {"test": "TEST-004"},
        {"test": "TEST-999"},
    ]

    expected = {
        "result": "non_empty",
        "exact_id_sets": {
            "TEST": ["TEST-004"],
        },
    }

    correct, issues = evaluate_retrieval(
        records,
        expected,
    )

    assert correct is False
    assert "id set mismatch" in issues[0]


def test_environment_counts_accept_row_per_result_shape():
    records = [
        {
            "environment": "SiL",
            "result": "PASS",
            "count": 4,
        },
        {
            "environment": "SiL",
            "result": "FAIL",
            "count": 1,
        },
    ]

    expected = {
        "result": "non_empty",
        "environment_result_counts": {
            "SiL": {
                "PASS": 4,
                "FAIL": 1,
            }
        },
    }

    correct, issues = evaluate_retrieval(
        records,
        expected,
    )

    assert correct is True
    assert issues == []


def test_environment_counts_accept_aggregated_shape():
    records = [
        {
            "environment": "SiL",
            "passCount": 4,
            "failCount": 1,
        }
    ]

    expected = {
        "result": "non_empty",
        "environment_result_counts": {
            "SiL": {
                "PASS": 4,
                "FAIL": 1,
            }
        },
    }

    correct, issues = evaluate_retrieval(
        records,
        expected,
    )

    assert correct is True
    assert issues == []


def test_empty_result_is_scored_correctly():
    correct, issues = evaluate_retrieval(
        [],
        {"result": "empty"},
    )

    assert correct is True
    assert issues == []


def test_no_result_answer_requires_clear_phrase():
    correct, issues = evaluate_answer(
        "No matching graph facts were retrieved.",
        {"result": "empty"},
    )

    assert correct is True
    assert issues == []


@pytest.mark.parametrize(
    ("execution", "retrieval", "answer", "expected"),
    [
        (True, True, True, "fully_correct"),
        (False, False, False, "execution_failure"),
        (True, False, False, "retrieval_failure"),
        (True, True, False, "answer_failure"),
    ],
)
def test_classifies_result_by_failure_stage(
    execution,
    retrieval,
    answer,
    expected,
):
    result = make_result(
        execution=execution,
        retrieval=retrieval,
        answer=answer,
    )

    assert classify_result(result) == expected


def test_build_summary_counts_outcomes():
    results = [
        make_result(),
        make_result(
            retrieval=False,
            answer=False,
        ),
    ]

    summary = build_summary(results)

    assert summary["total_cases"] == 2
    assert summary["fully_correct"] == 1
    assert summary["outcomes"]["fully_correct"] == 1
    assert summary["outcomes"]["retrieval_failure"] == 1


def test_write_results_includes_outcome(tmp_path):
    output = tmp_path / "results.json"

    write_results(
        output,
        benchmark_version=1,
        configured_model="auto",
        results=[make_result()],
    )

    data = json.loads(
        output.read_text(encoding="utf-8")
    )

    assert data["results"][0]["outcome"] == (
        "fully_correct"
    )