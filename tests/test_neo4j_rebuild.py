import pytest

from neo4j_rebuild import (
    CypherScriptError,
    RebuildSafetyError,
    expected_reset_confirmation,
    load_cypher_statements,
    validate_reset_safety,
)


def test_builds_expected_reset_confirmation():
    confirmation = expected_reset_confirmation("neo4j")

    assert confirmation == (
        "RESET bluetooth-reconnection-kg-poc/neo4j"
    )


@pytest.mark.parametrize(
    "uri",
    [
        "neo4j://localhost:7687",
        "bolt://127.0.0.1:7687",
        "neo4j://[::1]:7687",
    ],
)
def test_accepts_local_reset_with_exact_confirmation(uri):
    validate_reset_safety(
        uri=uri,
        database="neo4j",
        confirmation=(
            "RESET bluetooth-reconnection-kg-poc/neo4j"
        ),
    )


def test_rejects_non_local_neo4j_host():
    with pytest.raises(
        RebuildSafetyError,
        match="only for a local Neo4j instance",
    ):
        validate_reset_safety(
            uri="neo4j://example.com:7687",
            database="neo4j",
            confirmation=(
                "RESET bluetooth-reconnection-kg-poc/neo4j"
            ),
        )


def test_rejects_incorrect_reset_confirmation():
    with pytest.raises(
        RebuildSafetyError,
        match="confirmation does not match",
    ):
        validate_reset_safety(
            uri="neo4j://localhost:7687",
            database="neo4j",
            confirmation="WRONG",
        )


def test_loads_multiple_cypher_statements(tmp_path):
    script_path = tmp_path / "example.cypher"
    script_path.write_text(
        "MATCH (n) RETURN n;\nMATCH (m) RETURN m;\n",
        encoding="utf-8",
    )

    statements = load_cypher_statements(script_path)

    assert statements == [
        "MATCH (n) RETURN n",
        "MATCH (m) RETURN m",
    ]


def test_rejects_missing_cypher_script(tmp_path):
    missing_path = tmp_path / "missing.cypher"

    with pytest.raises(
        CypherScriptError,
        match="does not exist",
    ):
        load_cypher_statements(missing_path)


def test_rejects_empty_cypher_script(tmp_path):
    script_path = tmp_path / "empty.cypher"
    script_path.write_text("   \n", encoding="utf-8")

    with pytest.raises(
        CypherScriptError,
        match="is empty",
    ):
        load_cypher_statements(script_path)