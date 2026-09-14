from dataclasses import dataclass

from graph_retrieval_tool import (
    GraphRetrievalTool,
)
from llm_client import LLMClient
from query_service import QueryService


@dataclass(frozen=True)
class AgentResponse:
    question: str
    answer: str
    graph_tool_used: bool
    graph_tool_calls: int
    graph_tool_successes: int
    retrieved_record_count: int
    cypher_generation_attempts: int | None
    retry_reason: str | None
    tool_error: str | None


class AgentService:
    def __init__(
        self,
        llm_client: LLMClient,
        query_service: QueryService,
    ):
        self.llm = llm_client
        self.query_service = query_service

    async def answer_question(
        self,
        question: str,
    ) -> AgentResponse:
        graph_tool = GraphRetrievalTool(
            self.query_service
        )

        answer = await self.llm.run_agent(
            question=question,
            tools=[
                graph_tool.tool,
            ],
        )

        successful_call = (
            graph_tool.calls[0]
            if graph_tool.calls
            else None
        )

        tool_error = (
            graph_tool.errors[-1]
            if graph_tool.errors
            else None
        )

        return AgentResponse(
            question=question,
            answer=answer,
            graph_tool_used=(
                graph_tool.invocation_count > 0
            ),
            graph_tool_calls=(
                graph_tool.invocation_count
            ),
            graph_tool_successes=len(
                graph_tool.calls
            ),
            retrieved_record_count=(
                successful_call.record_count
                if successful_call
                else 0
            ),
            cypher_generation_attempts=(
                successful_call.generation_attempts
                if successful_call
                else None
            ),
            retry_reason=(
                successful_call.retry_reason
                if successful_call
                else None
            ),
            tool_error=tool_error,
        )