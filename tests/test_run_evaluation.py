import asyncio
from types import SimpleNamespace

from evaluation import BenchmarkCase
from run_evaluation import run_case


class SuccessfulService:
    async def answer_question(self, question):
        return SimpleNamespace(
            records=[
                {"requirement": "REQ-006"}
            ],
            answer=(
                "TEST-006 verifies requirement REQ-006."
            ),
            generation_attempts=1,
            cypher=(
                "MATCH (t:Test)-[:VERIFIES]->"
                "(r:Requirement) RETURN r.id"
            ),
        )


class FailingService:
    async def answer_question(self, question):
        raise RuntimeError("generation failed")


def test_run_case_scores_successful_pipeline_result():
    case = BenchmarkCase(
        id="EVAL-001",
        category="entity_lookup",
        question=(
            "What requirement does TEST-006 verify?"
        ),
        expected={
            "result": "non_empty",
            "required_values": ["REQ-006"],
        },
    )

    result = asyncio.run(
        run_case(
            SuccessfulService(),
            case,
        )
    )

    assert result.execution_success is True
    assert result.retrieval_correct is True
    assert result.answer_correct is True
    assert result.generation_attempts == 1


def test_run_case_captures_pipeline_exception():
    case = BenchmarkCase(
        id="EVAL-001",
        category="entity_lookup",
        question="Example question?",
        expected={
            "result": "non_empty",
        },
    )

    result = asyncio.run(
        run_case(
            FailingService(),
            case,
        )
    )

    assert result.execution_success is False
    assert result.retrieval_correct is False
    assert result.answer_correct is False
    assert result.error == "generation failed"