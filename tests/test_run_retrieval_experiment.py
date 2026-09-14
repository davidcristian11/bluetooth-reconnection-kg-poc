import asyncio
from pathlib import Path
from types import SimpleNamespace

import pytest

from flat_retriever import (
    LexicalFlatRetriever,
)
from retrieval_benchmark import (
    load_retrieval_benchmark,
)
from run_retrieval_experiment import (
    run_flat_case,
    run_graph_case,
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


class SuccessfulGraphService:
    async def retrieve_question(
        self,
        question,
    ):
        return SimpleNamespace(
            records=[
                {
                    "requirementId": (
                        "REQ-006"
                    )
                }
            ],
            cypher=(
                "MATCH "
                "(:Test {id: 'TEST-006'})"
                "-[:VERIFIES]->"
                "(r:Requirement) "
                "RETURN r.id AS requirementId"
            ),
            generation_attempts=1,
            retry_reason=None,
        )


class FailingGraphService:
    async def retrieve_question(
        self,
        question,
    ):
        raise RuntimeError(
            "graph retrieval failed"
        )


def test_flat_case_runner_returns_metrics():
    case = load_case("RET-001")

    retriever = (
        LexicalFlatRetriever.from_project_data(
            PROJECT_ROOT
        )
    )

    result = run_flat_case(
        retriever,
        case,
    )

    assert (
        result["execution_success"]
        is True
    )

    assert result["metrics"][
        "recall"
    ] == pytest.approx(1.0)

    assert (
        result["retrieved_count"]
        == 10
    )


def test_graph_case_runner_scores_retrieval_without_answer():
    case = load_case("RET-001")

    result = asyncio.run(
        run_graph_case(
            SuccessfulGraphService(),
            case,
        )
    )

    assert (
        result["execution_success"]
        is True
    )

    assert result["metrics"][
        "recall"
    ] == pytest.approx(1.0)

    assert result["metrics"][
        "precision"
    ] == pytest.approx(1.0)

    assert result["metrics"][
        "evidence_complete"
    ] is True

    assert (
        result["generation_attempts"]
        == 1
    )


def test_graph_case_runner_captures_failure():
    case = load_case("RET-001")

    result = asyncio.run(
        run_graph_case(
            FailingGraphService(),
            case,
        )
    )

    assert (
        result["execution_success"]
        is False
    )

    assert (
        result["metrics"]["recall"]
        == 0.0
    )

    assert result["metrics"][
        "evidence_complete"
    ] is False

    assert result["error"] == (
        "graph retrieval failed"
    )