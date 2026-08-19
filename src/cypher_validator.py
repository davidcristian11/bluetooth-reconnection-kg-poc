import re


FORBIDDEN_PATTERNS = [
    r"\bCREATE\b",
    r"\bMERGE\b",
    r"\bDELETE\b",
    r"\bDETACH\s+DELETE\b",
    r"\bSET\b",
    r"\bREMOVE\b",
    r"\bDROP\b",
    r"\bCALL\b",
    r"\bLOAD\s+CSV\b",
]


class CypherValidationError(ValueError):
    pass


class UnsafeCypherError(CypherValidationError):
    pass


def _remove_string_literals(cypher: str) -> str:
    return re.sub(
        r"""'(?:\\.|[^'\\])*'|"(?:\\.|[^"\\])*\"""",
        "''",
        cypher,
    )


def validate_cypher(cypher: str) -> None:
    if not cypher.strip():
        raise CypherValidationError(
            "Generated Cypher is empty."
        )

    query = cypher.strip()

    if query.endswith(";"):
        query = query[:-1]

    if ";" in query:
        raise UnsafeCypherError(
            "Only one Cypher statement is allowed."
        )

    query_without_strings = _remove_string_literals(
        query
    )

    for pattern in FORBIDDEN_PATTERNS:
        if re.search(
            pattern,
            query_without_strings,
            re.IGNORECASE,
        ):
            raise UnsafeCypherError(
                f"Forbidden Cypher operation detected: {pattern}"
            )

    if not re.search(
        r"\bMATCH\b",
        query_without_strings,
        re.IGNORECASE,
    ):
        raise CypherValidationError(
            "Generated Cypher must contain MATCH."
        )

    if not re.search(
        r"\bRETURN\b",
        query_without_strings,
        re.IGNORECASE,
    ):
        raise CypherValidationError(
            "Generated Cypher must contain RETURN."
        )