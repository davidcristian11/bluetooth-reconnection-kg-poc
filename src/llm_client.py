import os

from copilot import CopilotClient
from dotenv import load_dotenv

from schema import GRAPH_SCHEMA


load_dotenv()


class LLMClient:
    def __init__(self):
        if not os.getenv("COPILOT_GITHUB_TOKEN"):
            raise ValueError(
                "COPILOT_GITHUB_TOKEN is missing from .env"
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
        previous_error: str | None = None,
    ) -> str:
        correction_context = ""

        if previous_error:
            correction_context = f"""
A previous attempt failed.

Previous Cypher:
{previous_cypher}

Error:
{previous_error}

Generate a corrected query.
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
            model="auto",
            available_tools=[],
        ) as session:
            response = await session.send_and_wait(prompt)

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
- Do not describe something as a root cause unless the retrieved data explicitly models or states it as a root cause.
- When explaining defect information, prefer wording such as "The linked defect describes..." or "The retrieved evidence indicates...".
- You may explain relationships represented by the Cypher traversal.
- Do not invent or suggest node labels, relationships, or properties that are not present in the provided schema.
- If no records were retrieved, say that no matching graph facts were retrieved.
- Do not claim the database contains no data merely because the query returned no rows.
- If requested information is not represented in the graph, simply state that it is not available in the current graph model.
- Only suggest schema extensions if the user explicitly asks how the graph could be extended.
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
            model="auto",
            available_tools=[],
        ) as session:
            response = await session.send_and_wait(prompt)

        return response.data.content.strip()