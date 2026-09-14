from pathlib import Path

import pytest

from flat_retriever import (
    LexicalFlatRetriever,
)
from retrieval_benchmark import (
    load_retrieval_benchmark,
)
from retrieval_evaluation import (
    evaluate_retrieved_evidence,
    flat_results_to_records,
)


PROJECT_ROOT = Path(
    __file__
).resolve().parents[1]

BENCHMARK_PATH = (
    PROJECT_ROOT
    / "evaluation"
    / "retrieval_benchmark.yaml"
)


def load_case(case_id):
    _, cases = (
        load_retrieval_benchmark(
            BENCHMARK_PATH
        )
    )

    return next(
        case
        for case in cases
        if case.id == case_id
    )


def test_flat_multi_hop_case_exposes_missing_evidence():
    case = load_case("RET-005")

    retriever = (
        LexicalFlatRetriever.from_project_data(
            PROJECT_ROOT
        )
    )

    results = retriever.search(
        case.question,
        top_k=case.top_k,
    )

    metrics = evaluate_retrieved_evidence(
        flat_results_to_records(
            results
        ),
        case.expected,
    )

    assert metrics.recall == pytest.approx(
        0.8
    )

    assert metrics.precision == pytest.approx(
        0.8
    )

    assert (
        metrics.evidence_complete
        is False
    )

    assert set(
        metrics.missing_atoms
    ) == {
        "id:COMP-002",
        "id:REQ-002",
    }


def test_flat_cross_source_case_exposes_missing_sources():
    case = load_case("RET-007")

    retriever = (
        LexicalFlatRetriever.from_project_data(
            PROJECT_ROOT
        )
    )

    results = retriever.search(
        case.question,
        top_k=case.top_k,
    )

    metrics = evaluate_retrieved_evidence(
        flat_results_to_records(
            results
        ),
        case.expected,
    )

    assert metrics.recall == pytest.approx(
        4 / 6
    )

    assert metrics.precision == pytest.approx(
        1.0
    )

    assert (
        metrics.evidence_complete
        is False
    )

    assert set(
        metrics.missing_atoms
    ) == {
        (
            "source_system:"
            "DefectTrackingSystem"
        ),
        (
            "source_system:"
            "TraceRepository"
        ),
    }


def test_flat_aggregation_case_has_complete_evidence():
    case = load_case("RET-010")

    retriever = (
        LexicalFlatRetriever.from_project_data(
            PROJECT_ROOT
        )
    )

    results = retriever.search(
        case.question,
        top_k=case.top_k,
    )

    metrics = evaluate_retrieved_evidence(
        flat_results_to_records(
            results
        ),
        case.expected,
    )

    assert metrics.recall == pytest.approx(
        1.0
    )

    assert metrics.precision == pytest.approx(
        1.0
    )

    assert (
        metrics.evidence_complete
        is True
    )


def test_graph_style_direct_result_scores_perfectly():
    case = load_case("RET-001")

    metrics = evaluate_retrieved_evidence(
        [
            {
                "requirementId": (
                    "REQ-006"
                )
            }
        ],
        case.expected,
    )

    assert metrics.recall == pytest.approx(
        1.0
    )

    assert metrics.precision == pytest.approx(
        1.0
    )

    assert (
        metrics.evidence_complete
        is True
    )


def test_graph_style_aggregation_result_scores_perfectly():
    case = load_case("RET-010")

    records = [
        {
            "environment": "SiL",
            "passCount": 4,
            "failCount": 1,
        },
        {
            "environment": "HiL",
            "passCount": 2,
            "failCount": 2,
        },
        {
            "environment": "Vehicle",
            "passCount": 3,
            "failCount": 4,
        },
    ]

    metrics = evaluate_retrieved_evidence(
        records,
        case.expected,
    )

    assert metrics.recall == pytest.approx(
        1.0
    )

    assert metrics.precision == pytest.approx(
        1.0
    )

    assert (
        metrics.evidence_complete
        is True
    )