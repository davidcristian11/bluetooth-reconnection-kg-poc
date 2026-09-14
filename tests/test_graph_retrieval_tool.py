import asyncio
import json
from types import SimpleNamespace

from copilot import ToolInvocation

from graph_retrieval_tool import (
    GraphRetrievalTool,
)


class FakeQueryService:
    def __init__(self):
        self.questions = []

    async def retrieve_question(
        self,
        question,
    ):
        self.questions.append(question)

        return SimpleNamespace(
            question=question,
            cypher=(
                "MATCH "
                "(t:Test {id: 'TEST-006'})"
                "-[:VERIFIES]->"
                "(r:Requirement) "
                "RETURN r.id AS requirementId"
            ),
            records=[
                {
                    "requirementId": (
                        "REQ-006"
                    )
                }
            ],
            generation_attempts=1,
            retry_reason=None,
        )


def test_graph_tool_returns_retrieved_evidence():
    query_service = FakeQueryService()

    graph_tool = GraphRetrievalTool(
        query_service
    )

    result = asyncio.run(
        graph_tool.tool.handler(
            ToolInvocation(
                arguments={
                    "question": (
                        "What requirement does "
                        "TEST-006 verify?"
                    )
                }
            )
        )
    )

    assert result.result_type == "success"

    payload = json.loads(
        result.text_result_for_llm
    )

    assert payload["records"] == [
        {
            "requirementId": "REQ-006"
        }
    ]

    assert query_service.questions == [
        (
            "What requirement does "
            "TEST-006 verify?"
        )
    ]

    assert graph_tool.invocation_count == 1
    assert len(graph_tool.calls) == 1


def test_graph_tool_rejects_second_call():
    query_service = FakeQueryService()

    graph_tool = GraphRetrievalTool(
        query_service
    )

    first = ToolInvocation(
        arguments={
            "question": "Find TEST-006"
        }
    )

    second = ToolInvocation(
        arguments={
            "question": "Find REQ-006"
        }
    )

    first_result = asyncio.run(
        graph_tool.tool.handler(first)
    )

    second_result = asyncio.run(
        graph_tool.tool.handler(second)
    )

    assert (
        first_result.result_type
        == "success"
    )

    assert (
        second_result.result_type
        == "failure"
    )

    assert graph_tool.invocation_count == 2
    assert len(graph_tool.calls) == 1

    assert (
        "at most once"
        in second_result.error
    )


def test_graph_tool_rejects_missing_question():
    query_service = FakeQueryService()

    graph_tool = GraphRetrievalTool(
        query_service
    )

    result = asyncio.run(
        graph_tool.tool.handler(
            ToolInvocation(
                arguments={}
            )
        )
    )

    assert result.result_type == "failure"
    assert graph_tool.calls == []

    assert query_service.questions == []