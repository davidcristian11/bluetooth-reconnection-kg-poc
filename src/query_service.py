import json
import re
from dataclasses import dataclass

from neo4j.exceptions import Neo4jError

from cypher_validator import (
    CypherValidationError,
    UnsafeCypherError,
    validate_cypher,
)
from llm_client import LLMClient
from neo4j_client import (
    Neo4jClient,
    QueryResultLimitError,
)


MAX_CYPHER_ATTEMPTS = 2

ENTITY_ID_PATTERN = re.compile(
    r"\b[A-Z][A-Z0-9]*-\d+\b",
    flags=re.IGNORECASE,
)


@dataclass
class QueryResponse:
    question: str
    cypher: str
    records: list[dict]
    answer: str
    generation_attempts: int
    retry_reason: str | None


def extract_entity_ids(
    question: str,
) -> list[str]:
    seen = set()
    entity_ids = []

    for match in ENTITY_ID_PATTERN.findall(question):
        normalized = match.upper()

        if normalized in seen:
            continue

        seen.add(normalized)
        entity_ids.append(normalized)

    return entity_ids


class QueryService:
    def __init__(
        self,
        llm_client: LLMClient,
        neo4j_client: Neo4jClient,
    ):
        self.llm = llm_client
        self.neo4j = neo4j_client

    def _should_retry_empty_result(
        self,
        question: str,
    ) -> tuple[bool, list[str]]:
        referenced_ids = extract_entity_ids(question)

        if not referenced_ids:
            return False, []

        existing_ids = self.neo4j.find_existing_entity_ids(
            referenced_ids
        )

        all_referenced_ids_exist = (
            set(referenced_ids)
            <= existing_ids
        )

        return (
            all_referenced_ids_exist,
            referenced_ids,
        )

    async def answer_question(
        self,
        question: str,
    ) -> QueryResponse:
        previous_cypher = None
        previous_feedback = None
        retry_reason = None

        for attempt in range(
            1,
            MAX_CYPHER_ATTEMPTS + 1,
        ):
            cypher = await self.llm.generate_cypher(
                question=question,
                previous_cypher=previous_cypher,
                previous_feedback=previous_feedback,
            )

            try:
                validate_cypher(cypher)

                records = self.neo4j.run_query(cypher)

                if (
                    not records
                    and attempt < MAX_CYPHER_ATTEMPTS
                ):
                    (
                        should_retry,
                        referenced_ids,
                    ) = self._should_retry_empty_result(
                        question
                    )

                    if should_retry:
                        previous_cypher = cypher
                        previous_feedback = (
                            "The query executed successfully "
                            "but returned no records. "
                            "The entity IDs referenced in the "
                            "question exist in the graph: "
                            f"{', '.join(referenced_ids)}. "
                            "Review labels, relationship "
                            "directions, property names, and "
                            "filters, then generate the query "
                            "again."
                        )
                        retry_reason = (
                            "suspicious_empty_result"
                        )
                        continue

                break

            except UnsafeCypherError as error:
                raise RuntimeError(
                    "Unsafe Cypher was blocked. "
                    "No database modification was executed."
                ) from error

            except CypherValidationError as error:
                previous_cypher = cypher
                previous_feedback = str(error)
                retry_reason = "cypher_validation_error"

                if attempt == MAX_CYPHER_ATTEMPTS:
                    raise RuntimeError(
                        "Could not generate a valid Cypher query "
                        "after two attempts."
                    ) from error

            except QueryResultLimitError as error:
                previous_cypher = cypher
                previous_feedback = (
                    f"{error} Generate a more selective query "
                    "that answers the user's question without "
                    "returning unnecessary records."
                )
                retry_reason = "result_limit_error"

                if attempt == MAX_CYPHER_ATTEMPTS:
                    raise RuntimeError(
                        "Could not generate a sufficiently "
                        "selective Cypher query after two attempts."
                    ) from error

            except Neo4jError as error:
                previous_cypher = cypher
                previous_feedback = str(error)
                retry_reason = "neo4j_error"

                if attempt == MAX_CYPHER_ATTEMPTS:
                    raise RuntimeError(
                        "Could not execute a valid Cypher query "
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
            retry_reason=retry_reason,
        )