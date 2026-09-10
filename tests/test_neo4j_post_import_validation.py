from copy import deepcopy

import pytest

import neo4j_post_import_validation as validation
from neo4j_post_import_validation import (
    PostImportValidationError,
    calculate_graph_fingerprint,
    validate_exec_010_scenario,
    validate_post_import,
    validate_source_systems,
)


class FakeClient:
    def __init__(self, records):
        self.records = records
        self.calls = []

    def run_query(self, cypher, **parameters):
        self.calls.append(
            {
                "cypher": cypher,
                "parameters": parameters,
            }
        )
        return deepcopy(self.records)


class FingerprintClient:
    def __init__(self, nodes, relationships):
        self.nodes = nodes
        self.relationships = relationships

    def run_query(self, cypher, **parameters):
        if "MATCH (source)-[r]->(target)" in cypher:
            return deepcopy(self.relationships)

        return deepcopy(self.nodes)


def test_source_system_validation_accepts_expected_metadata(
    monkeypatch,
):
    monkeypatch.setattr(
        validation,
        "SOURCE_SYSTEM_BY_LABEL",
        {"Requirement": "RequirementsSystem"},
    )
    client = FakeClient([])

    issues = validate_source_systems(client)

    assert issues == []
    assert client.calls[0]["parameters"] == {
        "expected_source_system": "RequirementsSystem"
    }


def test_source_system_validation_rejects_mismatch(
    monkeypatch,
):
    monkeypatch.setattr(
        validation,
        "SOURCE_SYSTEM_BY_LABEL",
        {"Requirement": "RequirementsSystem"},
    )
    client = FakeClient(
        [
            {
                "id": "REQ-002",
                "source_system": "TestManagementSystem",
            }
        ]
    )

    issues = validate_source_systems(client)

    assert issues == [
        "Requirement 'REQ-002' has sourceSystem "
        "'TestManagementSystem'; expected 'RequirementsSystem'"
    ]


def test_exec_010_scenario_accepts_expected_path():
    client = FakeClient(
        [
            {
                "result": "FAIL",
                "environment": "Vehicle",
                "reconnection_time": 18.0,
                "trace_ids": [
                    "TRACE-006",
                    "TRACE-007",
                    "TRACE-008",
                ],
            }
        ]
    )

    issues = validate_exec_010_scenario(client)

    assert issues == []
    assert client.calls[0]["parameters"]["execution_id"] == (
        "EXEC-010"
    )


def test_exec_010_scenario_rejects_mismatch():
    client = FakeClient(
        [
            {
                "result": "PASS",
                "environment": "Vehicle",
                "reconnection_time": 18.0,
                "trace_ids": [
                    "TRACE-006",
                    "TRACE-007",
                    "TRACE-008",
                ],
            }
        ]
    )

    issues = validate_exec_010_scenario(client)

    assert len(issues) == 1
    assert "EXEC-010 scenario mismatch" in issues[0]


def test_graph_fingerprint_is_independent_of_query_order():
    nodes = [
        {
            "labels": ["Requirement"],
            "id": "REQ-002",
            "properties": {
                "id": "REQ-002",
                "status": "Approved",
            },
        },
        {
            "labels": ["Test"],
            "id": "TEST-002",
            "properties": {
                "id": "TEST-002",
            },
        },
    ]

    relationships = [
        {
            "source_labels": ["Test"],
            "source_id": "TEST-002",
            "relationship_type": "VERIFIES",
            "properties": {},
            "target_labels": ["Requirement"],
            "target_id": "REQ-002",
        }
    ]

    first = calculate_graph_fingerprint(
        FingerprintClient(nodes, relationships)
    )

    second = calculate_graph_fingerprint(
        FingerprintClient(
            list(reversed(nodes)),
            list(reversed(relationships)),
        )
    )

    assert first == second


def test_post_import_validation_raises_all_detected_issues(
    monkeypatch,
):
    monkeypatch.setattr(
        validation,
        "validate_counts",
        lambda client: (["count mismatch"], 52, 64),
    )
    monkeypatch.setattr(
        validation,
        "validate_duplicate_ids",
        lambda client: ["duplicate id"],
    )
    monkeypatch.setattr(
        validation,
        "validate_source_systems",
        lambda client: ["source-system mismatch"],
    )
    monkeypatch.setattr(
        validation,
        "validate_required_relationships",
        lambda client: [],
    )
    monkeypatch.setattr(
        validation,
        "validate_exec_010_scenario",
        lambda client: [],
    )

    with pytest.raises(
        PostImportValidationError,
        match="count mismatch",
    ) as exc_info:
        validate_post_import(object())

    assert "duplicate id" in str(exc_info.value)
    assert "source-system mismatch" in str(exc_info.value)