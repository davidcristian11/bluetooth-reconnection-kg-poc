import pytest

from neo4j_client import (
    Neo4jClient,
    QueryResultLimitError,
    _collect_limited_records,
)


class FakeRecord:
    def __init__(self, data):
        self._data = data

    def data(self):
        return self._data


class FakeResult:
    def __init__(self, records):
        self.records = [
            FakeRecord(record)
            for record in records
        ]
        self.consumed = False

    def fetch(self, amount):
        return self.records[:amount]

    def consume(self):
        self.consumed = True


def test_collects_records_within_limit():
    result = FakeResult(
        [
            {"id": "REQ-001"},
            {"id": "REQ-002"},
        ]
    )

    records = _collect_limited_records(
        result,
        max_records=2,
    )

    assert records == [
        {"id": "REQ-001"},
        {"id": "REQ-002"},
    ]

    assert result.consumed is True


def test_rejects_results_over_limit():
    result = FakeResult(
        [
            {"id": "REQ-001"},
            {"id": "REQ-002"},
        ]
    )

    with pytest.raises(
        QueryResultLimitError,
        match="more than 1 records",
    ):
        _collect_limited_records(
            result,
            max_records=1,
        )

    assert result.consumed is True


def test_find_existing_entity_ids_uses_parameterized_query():
    client = Neo4jClient.__new__(
        Neo4jClient
    )

    captured = {}

    def fake_run_query(
        cypher,
        parameters=None,
    ):
        captured["cypher"] = cypher
        captured["parameters"] = parameters

        return [
            {"id": "REQ-002"},
            {"id": "TEST-006"},
        ]

    client.run_query = fake_run_query

    result = client.find_existing_entity_ids(
        [
            "req-002",
            "TEST-006",
            "REQ-002",
        ]
    )

    assert result == {
        "REQ-002",
        "TEST-006",
    }

    assert captured["parameters"] == {
        "entity_ids": [
            "REQ-002",
            "TEST-006",
        ]
    }

    assert "$entity_ids" in captured["cypher"]