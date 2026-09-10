from dataclasses import dataclass
from pathlib import Path
import csv
import hashlib
import json

from neo4j_rebuild import Neo4jRebuildClient


PROJECT_ROOT = Path(__file__).resolve().parents[1]

NODE_SOURCES = {
    "Feature": PROJECT_ROOT / "data/nodes/features.csv",
    "Requirement": PROJECT_ROOT / "data/nodes/requirements.csv",
    "SoftwareComponent": (
        PROJECT_ROOT / "data/nodes/software_components.csv"
    ),
    "Test": PROJECT_ROOT / "data/nodes/tests.csv",
    "TestExecution": PROJECT_ROOT / "data/nodes/test_executions.csv",
    "TestTrace": PROJECT_ROOT / "data/nodes/test_traces.csv",
    "DefectTicket": PROJECT_ROOT / "data/nodes/defect_tickets.csv",
}

SOURCE_SYSTEM_BY_LABEL = {
    "Feature": "ProductDefinitionSystem",
    "Requirement": "RequirementsSystem",
    "SoftwareComponent": "SoftwareArchitectureSystem",
    "Test": "TestManagementSystem",
    "TestExecution": "TestManagementSystem",
    "TestTrace": "TraceRepository",
    "DefectTicket": "DefectTrackingSystem",
}


RELATIONSHIP_SOURCES = {
    "HAS_REQUIREMENT": (
        PROJECT_ROOT
        / "data/relationships/feature_has_requirement.csv"
    ),
    "IMPLEMENTS": (
        PROJECT_ROOT
        / "data/relationships/software_component_implements_requirement.csv"
    ),
    "VERIFIES": (
        PROJECT_ROOT
        / "data/relationships/test_verifies_requirement.csv"
    ),
    "EXECUTION_OF": (
        PROJECT_ROOT
        / "data/relationships/test_execution_execution_of_test.csv"
    ),
    "PRODUCES": (
        PROJECT_ROOT
        / "data/relationships/test_execution_produces_trace.csv"
    ),
    "HAS_DEFECT_TICKET": (
        PROJECT_ROOT
        / "data/relationships/test_execution_has_defect_ticket.csv"
    ),
    "AFFECTS": (
        PROJECT_ROOT
        / "data/relationships/defect_ticket_affects_component.csv"
    ),
}


class PostImportValidationError(RuntimeError):
    pass


@dataclass(frozen=True)
class RelationshipCoverageRule:
    name: str
    source_label: str
    relationship_type: str
    direction: str
    target_label: str
    minimum_matches: int = 1
    maximum_matches: int | None = None
    condition_property: str | None = None
    condition_value: str | None = None


RELATIONSHIP_COVERAGE_RULES = [
    RelationshipCoverageRule(
        name="feature_has_requirement",
        source_label="Feature",
        relationship_type="HAS_REQUIREMENT",
        direction="out",
        target_label="Requirement",
    ),
    RelationshipCoverageRule(
        name="requirement_belongs_to_feature",
        source_label="Requirement",
        relationship_type="HAS_REQUIREMENT",
        direction="in",
        target_label="Feature",
    ),
    RelationshipCoverageRule(
        name="approved_requirement_is_implemented",
        source_label="Requirement",
        relationship_type="IMPLEMENTS",
        direction="in",
        target_label="SoftwareComponent",
        condition_property="status",
        condition_value="Approved",
    ),
    RelationshipCoverageRule(
        name="approved_requirement_has_test_coverage",
        source_label="Requirement",
        relationship_type="VERIFIES",
        direction="in",
        target_label="Test",
        condition_property="status",
        condition_value="Approved",
    ),
    RelationshipCoverageRule(
        name="component_implements_requirement",
        source_label="SoftwareComponent",
        relationship_type="IMPLEMENTS",
        direction="out",
        target_label="Requirement",
    ),
    RelationshipCoverageRule(
        name="test_verifies_requirement",
        source_label="Test",
        relationship_type="VERIFIES",
        direction="out",
        target_label="Requirement",
    ),
    RelationshipCoverageRule(
        name="execution_has_exactly_one_test",
        source_label="TestExecution",
        relationship_type="EXECUTION_OF",
        direction="out",
        target_label="Test",
        minimum_matches=1,
        maximum_matches=1,
    ),
    RelationshipCoverageRule(
        name="trace_has_exactly_one_execution",
        source_label="TestTrace",
        relationship_type="PRODUCES",
        direction="in",
        target_label="TestExecution",
        minimum_matches=1,
        maximum_matches=1,
    ),
    RelationshipCoverageRule(
        name="defect_affects_component",
        source_label="DefectTicket",
        relationship_type="AFFECTS",
        direction="out",
        target_label="SoftwareComponent",
    ),
    RelationshipCoverageRule(
        name="defect_is_linked_to_execution",
        source_label="DefectTicket",
        relationship_type="HAS_DEFECT_TICKET",
        direction="in",
        target_label="TestExecution",
    ),
]


def count_csv_rows(path: Path) -> int:
    with path.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as file:
        return sum(1 for _ in csv.DictReader(file))


def validate_counts(
    client: Neo4jRebuildClient,
) -> tuple[list[str], int, int]:
    issues: list[str] = []

    expected_node_counts = {
        label: count_csv_rows(path)
        for label, path in NODE_SOURCES.items()
    }

    expected_relationship_counts = {
        relationship_type: count_csv_rows(path)
        for relationship_type, path in RELATIONSHIP_SOURCES.items()
    }

    expected_total_nodes = sum(expected_node_counts.values())
    expected_total_relationships = sum(
        expected_relationship_counts.values()
    )

    actual_total_nodes = client.run_query(
        "MATCH (n) RETURN count(n) AS count"
    )[0]["count"]

    actual_total_relationships = client.run_query(
        "MATCH ()-[r]->() RETURN count(r) AS count"
    )[0]["count"]

    if actual_total_nodes != expected_total_nodes:
        issues.append(
            "total node count mismatch: "
            f"expected {expected_total_nodes}, "
            f"found {actual_total_nodes}"
        )

    if actual_total_relationships != expected_total_relationships:
        issues.append(
            "total relationship count mismatch: "
            f"expected {expected_total_relationships}, "
            f"found {actual_total_relationships}"
        )

    for label, expected_count in expected_node_counts.items():
        actual_count = client.run_query(
            f"MATCH (n:{label}) RETURN count(n) AS count"
        )[0]["count"]

        if actual_count != expected_count:
            issues.append(
                f"{label} count mismatch: "
                f"expected {expected_count}, "
                f"found {actual_count}"
            )

    for relationship_type, expected_count in (
        expected_relationship_counts.items()
    ):
        actual_count = client.run_query(
            "MATCH ()-[r:"
            f"{relationship_type}"
            "]->() RETURN count(r) AS count"
        )[0]["count"]

        if actual_count != expected_count:
            issues.append(
                f"{relationship_type} count mismatch: "
                f"expected {expected_count}, "
                f"found {actual_count}"
            )

    return (
        issues,
        expected_total_nodes,
        expected_total_relationships,
    )


def validate_duplicate_ids(
    client: Neo4jRebuildClient,
) -> list[str]:
    issues: list[str] = []

    for label in NODE_SOURCES:
        duplicates = client.run_query(
            f"""
            MATCH (n:{label})
            WITH n.id AS id, count(*) AS duplicate_count
            WHERE id IS NULL OR duplicate_count > 1
            RETURN id, duplicate_count
            ORDER BY id
            """
        )

        for duplicate in duplicates:
            issues.append(
                f"{label} duplicate or missing id: "
                f"id={duplicate['id']!r}, "
                f"count={duplicate['duplicate_count']}"
            )

    return issues


def validate_source_systems(
    client: Neo4jRebuildClient,
) -> list[str]:
    issues: list[str] = []

    for label, expected_source_system in (
        SOURCE_SYSTEM_BY_LABEL.items()
    ):
        violations = client.run_query(
            f"""
            MATCH (n:{label})
            WHERE n.sourceSystem IS NULL
               OR n.sourceSystem <> $expected_source_system
            RETURN
                n.id AS id,
                n.sourceSystem AS source_system
            ORDER BY id
            """,
            expected_source_system=expected_source_system,
        )

        for violation in violations:
            issues.append(
                f"{label} {violation['id']!r} has sourceSystem "
                f"{violation['source_system']!r}; expected "
                f"{expected_source_system!r}"
            )

    return issues


def validate_required_relationships(
    client: Neo4jRebuildClient,
) -> list[str]:
    issues: list[str] = []

    for rule in RELATIONSHIP_COVERAGE_RULES:
        if rule.direction == "out":
            pattern = (
                f"(n)-[r:{rule.relationship_type}]->"
                f"(:{rule.target_label})"
            )
        else:
            pattern = (
                f"(n)<-[r:{rule.relationship_type}]-"
                f"(:{rule.target_label})"
            )

        condition = ""

        parameters = {
            "minimum_matches": rule.minimum_matches,
            "maximum_matches": rule.maximum_matches,
        }

        if rule.condition_property is not None:
            condition = (
                f"WHERE n.{rule.condition_property} = "
                "$condition_value"
            )
            parameters["condition_value"] = rule.condition_value

        violations = client.run_query(
            f"""
            MATCH (n:{rule.source_label})
            {condition}
            OPTIONAL MATCH {pattern}
            WITH n, count(r) AS relationship_count
            WHERE relationship_count < $minimum_matches
               OR (
                    $maximum_matches IS NOT NULL
                    AND relationship_count > $maximum_matches
               )
            RETURN n.id AS id, relationship_count
            ORDER BY id
            """,
            **parameters,
        )

        for violation in violations:
            issues.append(
                f"{rule.name}: {rule.source_label} "
                f"{violation['id']!r} has "
                f"{violation['relationship_count']} matching "
                "relationship(s)"
            )

    return issues


def validate_exec_010_scenario(
    client: Neo4jRebuildClient,
) -> list[str]:
    records = client.run_query(
        """
        MATCH (execution:TestExecution {id: $execution_id})
              -[:EXECUTION_OF]->
              (test:Test {id: $test_id})
        MATCH (test)-[:VERIFIES]->
              (requirement:Requirement {id: $requirement_id})
        MATCH (execution)-[:HAS_DEFECT_TICKET]->
              (defect:DefectTicket {id: $defect_id})
        MATCH (defect)-[:AFFECTS]->
              (component:SoftwareComponent {id: $component_id})
        MATCH (execution)-[:PRODUCES]->(trace:TestTrace)
        WITH execution, trace
        ORDER BY trace.id
        RETURN
            execution.result AS result,
            execution.environment AS environment,
            execution.reconnectionTimeSeconds AS reconnection_time,
            collect(trace.id) AS trace_ids
        """,
        execution_id="EXEC-010",
        test_id="TEST-002",
        requirement_id="REQ-002",
        defect_id="DEF-001",
        component_id="COMP-002",
    )

    if len(records) != 1:
        return [
            "EXEC-010 scenario is incomplete or ambiguous: "
            f"expected 1 result, found {len(records)}"
        ]

    actual = records[0]

    expected = {
        "result": "FAIL",
        "environment": "Vehicle",
        "reconnection_time": 18.0,
        "trace_ids": [
            "TRACE-006",
            "TRACE-007",
            "TRACE-008",
        ],
    }

    if actual != expected:
        return [
            "EXEC-010 scenario mismatch: "
            f"expected {expected}, found {actual}"
        ]

    return []


def calculate_graph_fingerprint(
    client: Neo4jRebuildClient,
) -> str:
    nodes = client.run_query(
        """
        MATCH (n)
        RETURN
            labels(n) AS labels,
            n.id AS id,
            properties(n) AS properties
        """
    )

    relationships = client.run_query(
        """
        MATCH (source)-[r]->(target)
        RETURN
            labels(source) AS source_labels,
            source.id AS source_id,
            type(r) AS relationship_type,
            properties(r) AS properties,
            labels(target) AS target_labels,
            target.id AS target_id
        """
    )

    for node in nodes:
        node["labels"] = sorted(node["labels"])

    for relationship in relationships:
        relationship["source_labels"] = sorted(
            relationship["source_labels"]
        )
        relationship["target_labels"] = sorted(
            relationship["target_labels"]
        )

    canonical_nodes = sorted(
        nodes,
        key=lambda item: json.dumps(
            item,
            sort_keys=True,
            default=str,
        ),
    )

    canonical_relationships = sorted(
        relationships,
        key=lambda item: json.dumps(
            item,
            sort_keys=True,
            default=str,
        ),
    )

    payload = {
        "nodes": canonical_nodes,
        "relationships": canonical_relationships,
    }

    serialized = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")

    return hashlib.sha256(serialized).hexdigest()


def validate_post_import(
    client: Neo4jRebuildClient,
) -> str:
    issues: list[str] = []

    count_issues, expected_nodes, expected_relationships = (
        validate_counts(client)
    )

    issues.extend(count_issues)
    issues.extend(validate_duplicate_ids(client))
    issues.extend(validate_source_systems(client))
    issues.extend(validate_required_relationships(client))
    issues.extend(validate_exec_010_scenario(client))

    if issues:
        formatted_issues = "\n".join(
            f"- {issue}" for issue in issues
        )

        raise PostImportValidationError(
            "Post-import validation failed:\n"
            f"{formatted_issues}"
        )

    fingerprint = calculate_graph_fingerprint(client)

    print(
        "Post-import validation passed: "
        f"{expected_nodes} nodes, "
        f"{expected_relationships} relationships, "
        "no duplicate IDs, source-system metadata valid, "
        "required relationships valid, EXEC-010 valid."
    )

    print(f"Graph fingerprint: {fingerprint}")

    return fingerprint