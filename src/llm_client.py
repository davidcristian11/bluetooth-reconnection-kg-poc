import os

from copilot import (
    CopilotClient,
    Tool,
)
from dotenv import load_dotenv

from schema import GRAPH_SCHEMA


load_dotenv()


AGENT_SYSTEM_PROMPT = """
You are a minimal engineering assistant for the Bluetooth
Reconnection Knowledge Graph proof of concept.

You have access to one tool:

graph_retrieval

Use graph_retrieval when the user asks for factual information
about the project's engineering data, including:

- Features
- Requirements
- SoftwareComponents
- Tests
- TestExecutions
- TestTraces
- DefectTickets
- source systems
- relationships between engineering entities
- filters, counts, comparisons, or patterns in the graph

Do not use graph_retrieval for:

- greetings
- general conversational questions
- general explanations of ontologies or Knowledge Graph concepts
- questions about what you can do
- questions that do not require facts from this project's graph

Tool rules:

- Call graph_retrieval at most once per user question.
- Pass the user's engineering question to the tool.
- Do not invent engineering facts before or after the tool call.
- When graph evidence is returned, answer using only those facts.
- If the retrieved evidence is insufficient, say so clearly.
- An empty graph retrieval result does not by itself prove that an
  entity does not exist in the Knowledge Graph.
- When no records are returned, say that no matching graph facts were
  retrieved for the question.
- Do not claim that an entity does not exist unless the retrieved
  evidence explicitly establishes that fact.
- If graph retrieval fails, say that the graph evidence could not
  be retrieved.
- Do not claim something is a root cause unless the retrieved
  evidence explicitly supports that statement.
- Keep the final answer concise.

For general conceptual questions that do not require project data,
answer directly without using the tool.
"""


class LLMClient:
    def __init__(self):
        if not os.getenv(
            "COPILOT_GITHUB_TOKEN"
        ):
            raise ValueError(
                "COPILOT_GITHUB_TOKEN is missing from .env"
            )

        self.model = (
            os.getenv(
                "COPILOT_MODEL",
                "auto",
            ).strip()
            or "auto"
        )

        self.client = CopilotClient()

    async def start(self) -> None:
        await self.client.start()

    async def stop(self) -> None:
        await self.client.stop()

    async def generate_cypher(
        self,
        question: str,
        previous_cypher: str | None = None,
        previous_feedback: str | None = None,
    ) -> str:
        correction_context = ""

        if previous_feedback:
            correction_context = f"""
A previous query attempt needs review.

Previous Cypher:
{previous_cypher}

Feedback:
{previous_feedback}

Generate a corrected query. Preserve any parts of the previous query
that were already correct.
"""

        prompt = f"""
You generate Cypher queries for a Neo4j Knowledge Graph.

Use ONLY this ontology/schema:

{GRAPH_SCHEMA}

Rules:
- Use only labels, relationships, and properties from the schema.
- Use known property values exactly as listed.
- Use ontology relationships to determine how concepts are connected.
- Generate exactly one read-only Cypher query.
- Never use CREATE, MERGE, DELETE, DETACH DELETE,
  SET, REMOVE, DROP, CALL, or LOAD CSV.
- Return enough explicit properties to answer the question.
- When traversal is important, return identifiers from relevant
  intermediate nodes.
- For explanation or "why" questions, retrieve the concrete evidence
  needed to support the explanation, including relevant measured and
  expected values when represented in the graph.
- For aggregation questions, return the grouping dimensions and
  aggregate values with clear aliases.
- Prefer required MATCH relationships when the related entity is
  necessary to answer the question.
- Use OPTIONAL MATCH only when missing related data should still keep
  the primary entity in the result.
- Prefer node.id, node.title, node.name, and relevant properties
  instead of returning whole nodes.
- Do not invent labels, relationships, properties, or enum values.
- Return only Cypher.
- Do not use markdown code fences.

Question:
{question}

{correction_context}
"""

        async with await self.client.create_session(
            model=self.model,
            available_tools=[],
        ) as session:
            response = await session.send_and_wait(
                prompt
            )

        return response.data.content.strip()

    async def generate_answer(
        self,
        question: str,
        cypher: str,
        graph_result: str,
    ) -> str:
        prompt = f"""
Answer the engineering question using ONLY the retrieved Neo4j facts.

Rules:
- Do not invent engineering facts.
- Do not describe something as a root cause unless the retrieved data
  explicitly models or states it as a root cause.
- When explaining defect information, prefer wording such as
  "The linked defect describes..." or
  "The retrieved evidence indicates...".
- You may explain relationships represented by the Cypher traversal.
- Do not invent or suggest node labels, relationships, or properties
  that are not present in the provided schema.
- If no records were retrieved, say that no matching graph facts were
  retrieved.
- Do not claim the database contains no data merely because the query
  returned no rows.
- If requested information is not represented in the graph, simply
  state that it is not available in the current graph model.
- Only suggest schema extensions if the user explicitly asks how the
  graph could be extended.
- If the evidence is insufficient, say so clearly.
- Keep the answer concise.

Question:
{question}

Cypher used for retrieval:
{cypher}

Retrieved Neo4j facts:
{graph_result}
"""

        async with await self.client.create_session(
            model=self.model,
            available_tools=[],
        ) as session:
            response = await session.send_and_wait(
                prompt
            )

        return response.data.content.strip()

    async def run_agent(
        self,
        question: str,
        tools: list[Tool],
    ) -> str:
        if not tools:
            raise ValueError(
                "Agent requires at least one tool."
            )

        available_tools = [
            f"custom:{tool.name}"
            for tool in tools
        ]

        async with await self.client.create_session(
            model=self.model,
            tools=tools,
            available_tools=available_tools,
            system_message={
                "mode": "append",
                "content": AGENT_SYSTEM_PROMPT,
            },
        ) as session:
            response = await session.send_and_wait(
                question
            )

        if (
            response is None
            or response.data is None
            or not hasattr(
                response.data,
                "content",
            )
        ):
            raise RuntimeError(
                "Agent returned no final response."
            )

        return response.data.content.strip()