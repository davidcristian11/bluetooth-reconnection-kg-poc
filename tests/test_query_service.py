import asyncio

import pytest

from neo4j_client import QueryResultLimitError
from query_service import (
    QueryService,
    extract_entity_ids,
)


class FakeLLMClient:
    def __init__(
        self,
        cypher_responses,
        answer="Generated answer",
    ):
        self.cypher_responses = cypher_responses
        self.answer = answer
        self.generation_calls = []
        self.answer_calls = []

    async def generate_cypher(
        self,
        question,
        previous_cypher=None,
        previous_feedback=None,
    ):
        self.generation_calls.append(
            {
                "question": question,
                "previous_cypher": previous_cypher,
                "previous_feedback": previous_feedback,
            }
        )

        response_index = (
            len(self.generation_calls) - 1
        )

        return self.cypher_responses[
            response_index
        ]

    async def generate_answer(
        self,
        question,
        cypher,
        graph_result,
    ):
        self.answer_calls.append(
            {
                "question": question,
                "cypher": cypher,
                "graph_result": graph_result,
            }
        )

        return self.answer


class FakeNeo4jClient:
    def __init__(
        self,
        query_responses,
        existing_ids=None,
    ):
        self.query_responses = query_responses
        self.existing_ids = set(
            existing_ids or []
        )
        self.queries = []
        self.existence_checks = []

    def run_query(
        self,
        cypher,
        parameters=None,
    ):
        self.queries.append(cypher)

        index = len(self.queries) - 1

        response = self.query_responses[index]

        if isinstance(response, Exception):
            raise response

        return response

    def find_existing_entity_ids(
        self,
        entity_ids,
    ):
        self.existence_checks.append(entity_ids)

        return (
            set(entity_ids)
            & self.existing_ids
        )


def test_extracts_unique_entity_ids():
    assert extract_entity_ids(
        "Compare req-002 with TEST-006 and REQ-002."
    ) == [
        "REQ-002",
        "TEST-006",
    ]


def test_successful_question_pipeline():
    llm = FakeLLMClient(
        cypher_responses=[
            "MATCH (r:Requirement {id: 'REQ-002'}) "
            "RETURN r.id AS requirementId"
        ],
        answer="EXEC-010 verifies REQ-002.",
    )

    neo4j = FakeNeo4jClient(
        query_responses=[
            [{"requirementId": "REQ-002"}]
        ]
    )

    service = QueryService(
        llm,
        neo4j,
    )

    response = asyncio.run(
        service.answer_question(
            "What requirement does EXEC-010 verify?"
        )
    )

    assert response.generation_attempts == 1
    assert response.retry_reason is None
    assert response.records == [
        {"requirementId": "REQ-002"}
    ]
    assert len(neo4j.queries) == 1


def test_invalid_query_is_corrected_once():
    llm = FakeLLMClient(
        cypher_responses=[
            "MATCH (n)",
            "MATCH (n) RETURN n.id AS id",
        ]
    )

    neo4j = FakeNeo4jClient(
        query_responses=[
            [{"id": "EXEC-010"}]
        ]
    )

    service = QueryService(
        llm,
        neo4j,
    )

    response = asyncio.run(
        service.answer_question(
            "Find EXEC-010"
        )
    )

    assert response.generation_attempts == 2
    assert response.retry_reason == (
        "cypher_validation_error"
    )

    assert len(llm.generation_calls) == 2
    assert len(neo4j.queries) == 1

    correction_call = (
        llm.generation_calls[1]
    )

    assert correction_call[
        "previous_cypher"
    ] == "MATCH (n)"

    assert (
        "must contain RETURN"
        in correction_call[
            "previous_feedback"
        ]
    )


def test_unsafe_query_is_blocked_without_retry():
    llm = FakeLLMClient(
        cypher_responses=[
            "MATCH (n) DELETE n RETURN n"
        ]
    )

    neo4j = FakeNeo4jClient(
        query_responses=[]
    )

    service = QueryService(
        llm,
        neo4j,
    )

    with pytest.raises(
        RuntimeError,
        match="Unsafe Cypher was blocked",
    ):
        asyncio.run(
            service.answer_question(
                "Delete everything"
            )
        )

    assert len(llm.generation_calls) == 1
    assert neo4j.queries == []
    assert llm.answer_calls == []


def test_empty_result_for_missing_id_is_not_retried():
    llm = FakeLLMClient(
        cypher_responses=[
            "MATCH (n:Requirement {id: 'REQ-999'}) "
            "RETURN n.id AS id"
        ],
        answer=(
            "No matching graph facts were retrieved."
        ),
    )

    neo4j = FakeNeo4jClient(
        query_responses=[
            [],
        ],
        existing_ids=set(),
    )

    service = QueryService(
        llm,
        neo4j,
    )

    response = asyncio.run(
        service.answer_question(
            "Find REQ-999"
        )
    )

    assert response.generation_attempts == 1
    assert response.retry_reason is None
    assert response.records == []
    assert len(llm.generation_calls) == 1

    assert neo4j.existence_checks == [
        ["REQ-999"]
    ]

    assert (
        llm.answer_calls[0]["graph_result"]
        == "[]"
    )


def test_empty_result_for_existing_id_is_retried():
    llm = FakeLLMClient(
        cypher_responses=[
            "MATCH (r:Requirement {id: 'REQ-002'}) "
            "MATCH (r)<-[:VERIFIES]-(t:Test) "
            "WHERE t.id = 'TEST-999' "
            "RETURN r.id",
            "MATCH (r:Requirement {id: 'REQ-002'}) "
            "RETURN r.id AS id",
        ]
    )

    neo4j = FakeNeo4jClient(
        query_responses=[
            [],
            [{"id": "REQ-002"}],
        ],
        existing_ids={
            "REQ-002",
        },
    )

    service = QueryService(
        llm,
        neo4j,
    )

    response = asyncio.run(
        service.answer_question(
            "Find requirement REQ-002"
        )
    )

    assert response.generation_attempts == 2
    assert response.retry_reason == (
        "suspicious_empty_result"
    )

    assert response.records == [
        {"id": "REQ-002"}
    ]

    assert len(llm.generation_calls) == 2
    assert len(neo4j.queries) == 2

    assert (
        "returned no records"
        in llm.generation_calls[1][
            "previous_feedback"
        ]
    )


def test_second_empty_result_is_accepted():
    llm = FakeLLMClient(
        cypher_responses=[
            "MATCH (r:Requirement {id: 'REQ-002'}) "
            "RETURN r.id",
            "MATCH (r:Requirement {id: 'REQ-002'}) "
            "RETURN r.id",
        ],
        answer=(
            "No matching graph facts were retrieved."
        ),
    )

    neo4j = FakeNeo4jClient(
        query_responses=[
            [],
            [],
        ],
        existing_ids={
            "REQ-002",
        },
    )

    service = QueryService(
        llm,
        neo4j,
    )

    response = asyncio.run(
        service.answer_question(
            "Find information related to REQ-002"
        )
    )

    assert response.generation_attempts == 2
    assert response.retry_reason == (
        "suspicious_empty_result"
    )

    assert response.records == []
    assert len(neo4j.queries) == 2


def test_result_limit_error_is_retried():
    llm = FakeLLMClient(
        cypher_responses=[
            "MATCH (n) RETURN n.id AS id",
            "MATCH (n:Requirement) "
            "RETURN n.id AS id",
        ]
    )

    neo4j = FakeNeo4jClient(
        query_responses=[
            QueryResultLimitError(
                "Neo4j query returned more than 100 records."
            ),
            [{"id": "REQ-002"}],
        ]
    )

    service = QueryService(
        llm,
        neo4j,
    )

    response = asyncio.run(
        service.answer_question(
            "Find requirements"
        )
    )

    assert response.generation_attempts == 2
    assert response.retry_reason == (
        "result_limit_error"
    )

    assert (
        "more selective query"
        in llm.generation_calls[1][
            "previous_feedback"
        ]
    )


def test_fails_after_two_invalid_queries():
    llm = FakeLLMClient(
        cypher_responses=[
            "MATCH (n)",
            "MATCH (m)",
        ]
    )

    neo4j = FakeNeo4jClient(
        query_responses=[]
    )

    service = QueryService(
        llm,
        neo4j,
    )

    with pytest.raises(
        RuntimeError,
        match="after two attempts",
    ):
        asyncio.run(
            service.answer_question(
                "Find something"
            )
        )

    assert len(llm.generation_calls) == 2
    assert neo4j.queries == []
    assert llm.answer_calls == []