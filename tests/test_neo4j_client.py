import pytest

from neo4j_client import (
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