import asyncio

import pytest

from query_service import QueryService


class FakeLLMClient:
    def __init__(self, cypher_responses, answer="Generated answer"):
        self.cypher_responses = cypher_responses
        self.answer = answer
        self.generation_calls = []
        self.answer_calls = []

    async def generate_cypher(
        self,
        question,
        previous_cypher=None,
        previous_error=None,
    ):
        self.generation_calls.append(
            {
                "question": question,
                "previous_cypher": previous_cypher,
                "previous_error": previous_error,
            }
        )

        response_index = len(self.generation_calls) - 1
        return self.cypher_responses[response_index]

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
    def __init__(self, records):
        self.records = records
        self.queries = []

    def run_query(self, cypher):
        self.queries.append(cypher)
        return self.records


def test_successful_question_pipeline():
    llm = FakeLLMClient(
        cypher_responses=[
            "MATCH (r:Requirement {id: 'REQ-002'}) "
            "RETURN r.id AS requirementId"
        ],
        answer="EXEC-010 verifies REQ-002.",
    )

    neo4j = FakeNeo4jClient(
        records=[{"requirementId": "REQ-002"}]
    )

    service = QueryService(llm, neo4j)

    response = asyncio.run(
        service.answer_question(
            "What requirement does EXEC-010 verify?"
        )
    )

    assert response.generation_attempts == 1
    assert response.records == [{"requirementId": "REQ-002"}]
    assert response.answer == "EXEC-010 verifies REQ-002."
    assert len(neo4j.queries) == 1
    assert '"REQ-002"' in llm.answer_calls[0]["graph_result"]


def test_invalid_query_is_corrected_once():
    llm = FakeLLMClient(
        cypher_responses=[
            "MATCH (n)",
            "MATCH (n) RETURN n.id AS id",
        ]
    )

    neo4j = FakeNeo4jClient(records=[{"id": "EXEC-010"}])
    service = QueryService(llm, neo4j)

    response = asyncio.run(
        service.answer_question("Find EXEC-010")
    )

    assert response.generation_attempts == 2
    assert len(llm.generation_calls) == 2
    assert len(neo4j.queries) == 1

    correction_call = llm.generation_calls[1]

    assert correction_call["previous_cypher"] == "MATCH (n)"
    assert "must contain RETURN" in correction_call[
        "previous_error"
    ]


def test_unsafe_query_is_blocked_without_retry():
    llm = FakeLLMClient(
        cypher_responses=[
            "MATCH (n) DELETE n RETURN n"
        ]
    )

    neo4j = FakeNeo4jClient(records=[])
    service = QueryService(llm, neo4j)

    with pytest.raises(
        RuntimeError,
        match="Unsafe Cypher was blocked",
    ):
        asyncio.run(
            service.answer_question("Delete everything")
        )

    assert len(llm.generation_calls) == 1
    assert neo4j.queries == []
    assert llm.answer_calls == []


def test_empty_result_is_not_retried():
    llm = FakeLLMClient(
        cypher_responses=[
            "MATCH (n:Requirement {id: 'REQ-999'}) "
            "RETURN n.id AS id"
        ],
        answer="No matching graph facts were retrieved.",
    )

    neo4j = FakeNeo4jClient(records=[])
    service = QueryService(llm, neo4j)

    response = asyncio.run(
        service.answer_question("Find REQ-999")
    )

    assert response.generation_attempts == 1
    assert response.records == []
    assert len(llm.generation_calls) == 1
    assert llm.answer_calls[0]["graph_result"] == "[]"


def test_fails_after_two_invalid_queries():
    llm = FakeLLMClient(
        cypher_responses=[
            "MATCH (n)",
            "MATCH (m)",
        ]
    )

    neo4j = FakeNeo4jClient(records=[])
    service = QueryService(llm, neo4j)

    with pytest.raises(
        RuntimeError,
        match="after two attempts",
    ):
        asyncio.run(
            service.answer_question("Find something")
        )

    assert len(llm.generation_calls) == 2
    assert neo4j.queries == []
    assert llm.answer_calls == []