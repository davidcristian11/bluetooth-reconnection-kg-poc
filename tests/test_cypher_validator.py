import pytest

from src.cypher_validator import (
    CypherValidationError,
    UnsafeCypherError,
    validate_cypher,
)


@pytest.mark.parametrize(
    "cypher",
    [
        "MATCH (n) RETURN n",
        "MATCH (n) RETURN n;",
        "MATCH (n) WHERE n.message = 'DELETE' RETURN n",
    ],
)
def test_accepts_read_queries(cypher):
    validate_cypher(cypher)


def test_rejects_empty_query():
    with pytest.raises(CypherValidationError):
        validate_cypher("   ")


def test_requires_match():
    with pytest.raises(CypherValidationError):
        validate_cypher("RETURN 1")


def test_requires_return():
    with pytest.raises(CypherValidationError):
        validate_cypher("MATCH (n)")


@pytest.mark.parametrize(
    "operation",
    [
        "CREATE (:Injected)",
        "MERGE (:Injected)",
        "DELETE n",
        "SET n.value = 1",
        "REMOVE n.value",
        "DROP INDEX example",
        "CALL db.labels()",
        "LOAD CSV FROM 'file:///data.csv' AS row",
    ],
)
def test_blocks_forbidden_operations(operation):
    cypher = f"MATCH (n) {operation} RETURN n"

    with pytest.raises(UnsafeCypherError):
        validate_cypher(cypher)


def test_rejects_multiple_statements():
    with pytest.raises(UnsafeCypherError):
        validate_cypher("MATCH (n) RETURN n; MATCH (m) RETURN m")


def test_blocks_insert():
    with pytest.raises(UnsafeCypherError):
        validate_cypher("MATCH (n) INSERT (:Injected) RETURN n")


def test_allows_semicolon_inside_string_literal():
    validate_cypher(
        "MATCH (n) WHERE n.message = 'first; second' RETURN n"
    )


def test_ignores_forbidden_words_inside_comments():
    validate_cypher(
        "MATCH (n) // CREATE is mentioned only in a comment\n"
        "RETURN n"
    )


def test_blocks_load_csv_with_comment_between_keywords():
    with pytest.raises(UnsafeCypherError):
        validate_cypher(
            "LOAD/* comment */CSV "
            "FROM 'file:///data.csv' AS row "
            "MATCH (n) RETURN row"
        )


def test_does_not_count_match_inside_comment():
    with pytest.raises(CypherValidationError):
        validate_cypher(
            "// MATCH\n"
            "SHOW USERS YIELD user RETURN user"
        )