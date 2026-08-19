import json
from dataclasses import dataclass

from neo4j.exceptions import Neo4jError

from cypher_validator import (
    CypherValidationError,
    UnsafeCypherError,
    validate_cypher,
)
from llm_client import LLMClient
from neo4j_client import Neo4jClient


@dataclass
class QueryResponse:
    question: str
    cypher: str
    records: list[dict]
    answer: str
    generation_attempts: int


class QueryService:
    def __init__(
        self,
        llm_client: LLMClient,
        neo4j_client: Neo4jClient,
    ):
        self.llm = llm_client
        self.neo4j = neo4j_client

    async def answer_question(
        self,
        question: str,
    ) -> QueryResponse:
        previous_cypher = None
        previous_error = None

        for attempt in range(1, 3):
            cypher = await self.llm.generate_cypher(
                question=question,
                previous_cypher=previous_cypher,
                previous_error=previous_error,
            )

            try:
                validate_cypher(cypher)

                records = self.neo4j.run_query(cypher)

                break

            except UnsafeCypherError as error:
                raise RuntimeError(
                    "Unsafe Cypher was blocked. "
                    "No database modification was executed."
                ) from error

            except (
                CypherValidationError,
                Neo4jError,
            ) as error:
                previous_cypher = cypher
                previous_error = str(error)

                if attempt == 2:
                    raise RuntimeError(
                        "Could not generate a valid Cypher query "
                        "after two attempts."
                    ) from error

        graph_result = json.dumps(
            records,
            indent=2,
            default=str,
        )

        answer = await self.llm.generate_answer(
            question=question,
            cypher=cypher,
            graph_result=graph_result,
        )

        return QueryResponse(
            question=question,
            cypher=cypher,
            records=records,
            answer=answer,
            generation_attempts=attempt,
        )