import json
from dataclasses import dataclass

from copilot import (
    Tool,
    ToolInvocation,
    ToolResult,
)

from query_service import QueryService


GRAPH_RETRIEVAL_TOOL_NAME = "graph_retrieval"


@dataclass(frozen=True)
class GraphToolCall:
    question: str
    cypher: str
    record_count: int
    generation_attempts: int
    retry_reason: str | None


class GraphRetrievalTool:
    def __init__(
        self,
        query_service: QueryService,
    ):
        self.query_service = query_service

        self.invocation_count = 0
        self.calls: list[GraphToolCall] = []
        self.errors: list[str] = []

        self.tool = Tool(
            name=GRAPH_RETRIEVAL_TOOL_NAME,
            description=(
                "Retrieve factual engineering evidence from the "
                "Bluetooth reconnection Knowledge Graph. Use this "
                "tool for questions about graph entities, "
                "requirements, tests, executions, traces, defects, "
                "software components, source systems, engineering "
                "relationships, counts, filters, or patterns."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": (
                            "The engineering question to retrieve "
                            "evidence for."
                        ),
                    }
                },
                "required": [
                    "question",
                ],
                "additionalProperties": False,
            },
            handler=self._handle,
            skip_permission=True,
            defer="never",
        )

    async def _handle(
        self,
        invocation: ToolInvocation,
    ) -> ToolResult:
        self.invocation_count += 1

        if self.invocation_count > 1:
            error = (
                "graph_retrieval may be called at most once "
                "per user question."
            )

            self.errors.append(error)

            return ToolResult(
                text_result_for_llm=(
                    "The graph retrieval tool has already been "
                    "used for this question. Use the evidence "
                    "already returned and do not call it again."
                ),
                result_type="failure",
                error=error,
            )

        arguments = invocation.arguments or {}

        if not isinstance(arguments, dict):
            error = (
                "graph_retrieval arguments must be an object."
            )

            self.errors.append(error)

            return ToolResult(
                text_result_for_llm=(
                    "Invalid graph retrieval arguments."
                ),
                result_type="failure",
                error=error,
            )

        question = arguments.get("question")

        if (
            not isinstance(question, str)
            or not question.strip()
        ):
            error = (
                "graph_retrieval requires a non-empty question."
            )

            self.errors.append(error)

            return ToolResult(
                text_result_for_llm=(
                    "A non-empty engineering question is "
                    "required for graph retrieval."
                ),
                result_type="failure",
                error=error,
            )

        question = question.strip()

        try:
            response = (
                await self.query_service.retrieve_question(
                    question
                )
            )

        except Exception as error:
            self.errors.append(str(error))

            return ToolResult(
                text_result_for_llm=(
                    "Graph retrieval failed. Do not invent "
                    "engineering facts. Explain that the "
                    "requested graph evidence could not be "
                    "retrieved."
                ),
                result_type="failure",
                error=str(error),
            )

        self.calls.append(
            GraphToolCall(
                question=question,
                cypher=response.cypher,
                record_count=len(response.records),
                generation_attempts=(
                    response.generation_attempts
                ),
                retry_reason=response.retry_reason,
            )
        )

        payload = {
            "question": response.question,
            "cypher": response.cypher,
            "records": response.records,
            "retrievalMetadata": {
                "generationAttempts": (
                    response.generation_attempts
                ),
                "retryReason": (
                    response.retry_reason
                ),
            },
        }

        return ToolResult(
            text_result_for_llm=json.dumps(
                payload,
                indent=2,
                default=str,
            ),
            result_type="success",
        )