import asyncio
from types import SimpleNamespace

from copilot import ToolInvocation

from agent_service import AgentService


class FakeQueryService:
    async def retrieve_question(
        self,
        question,
    ):
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


class FakeAgentLLM:
    def __init__(
        self,
        *,
        use_tool,
        answer,
    ):
        self.use_tool = use_tool
        self.answer = answer
        self.calls = []

    async def run_agent(
        self,
        question,
        tools,
    ):
        self.calls.append(
            {
                "question": question,
                "tools": tools,
            }
        )

        if self.use_tool:
            await tools[0].handler(
                ToolInvocation(
                    arguments={
                        "question": question
                    }
                )
            )

        return self.answer


def test_agent_reports_graph_tool_usage():
    llm = FakeAgentLLM(
        use_tool=True,
        answer=(
            "TEST-006 verifies REQ-006."
        ),
    )

    service = AgentService(
        llm_client=llm,
        query_service=FakeQueryService(),
    )

    response = asyncio.run(
        service.answer_question(
            "What requirement does "
            "TEST-006 verify?"
        )
    )

    assert response.graph_tool_used is True
    assert response.graph_tool_calls == 1
    assert response.graph_tool_successes == 1
    assert response.retrieved_record_count == 1

    assert (
        response.cypher_generation_attempts
        == 1
    )

    assert response.retry_reason is None

    assert response.answer == (
        "TEST-006 verifies REQ-006."
    )


def test_agent_can_answer_without_graph_tool():
    llm = FakeAgentLLM(
        use_tool=False,
        answer=(
            "A Knowledge Graph represents "
            "entities and their relationships."
        ),
    )

    service = AgentService(
        llm_client=llm,
        query_service=FakeQueryService(),
    )

    response = asyncio.run(
        service.answer_question(
            "What is a Knowledge Graph?"
        )
    )

    assert response.graph_tool_used is False
    assert response.graph_tool_calls == 0
    assert response.graph_tool_successes == 0
    assert response.retrieved_record_count == 0

    assert (
        response.cypher_generation_attempts
        is None
    )