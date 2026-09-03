import re


FORBIDDEN_PATTERNS = [
    r"\bCREATE\b",
    r"\bINSERT\b",
    r"\bMERGE\b",
    r"\bDELETE\b",
    r"\bDETACH\s+DELETE\b",
    r"\bSET\b",
    r"\bREMOVE\b",
    r"\bDROP\b",
    r"\bCALL\b",
    r"\bLOAD\s+CSV\b",
]

STRING_LITERAL_PATTERN = (
    r"'(?:\\.|[^'\\])*'"
    r'|"(?:\\.|[^"\\])*"'
)


class CypherValidationError(ValueError):
    pass


class UnsafeCypherError(CypherValidationError):
    pass


def _remove_string_literals(cypher: str) -> str:
    return re.sub(
        STRING_LITERAL_PATTERN,
        "''",
        cypher,
    )


def _remove_comments(cypher: str) -> str:
    return re.sub(
        r"/\*.*?\*/|//[^\r\n]*",
        " ",
        cypher,
        flags=re.DOTALL,
    )


def validate_cypher(cypher: str) -> None:
    if not cypher.strip():
        raise CypherValidationError(
            "Generated Cypher is empty."
        )

    query_for_validation = _remove_string_literals(
        cypher.strip()
    )

    query_for_validation = _remove_comments(
        query_for_validation
    ).strip()

    if query_for_validation.endswith(";"):
        query_for_validation = (
            query_for_validation[:-1].rstrip()
        )

    if ";" in query_for_validation:
        raise UnsafeCypherError(
            "Only one Cypher statement is allowed."
        )

    for pattern in FORBIDDEN_PATTERNS:
        if re.search(
            pattern,
            query_for_validation,
            re.IGNORECASE,
        ):
            raise UnsafeCypherError(
                "Forbidden Cypher operation detected: "
                f"{pattern}"
            )

    if not re.search(
        r"\bMATCH\b",
        query_for_validation,
        re.IGNORECASE,
    ):
        raise CypherValidationError(
            "Generated Cypher must contain MATCH."
        )

    if not re.search(
        r"\bRETURN\b",
        query_for_validation,
        re.IGNORECASE,
    ):
        raise CypherValidationError(
            "Generated Cypher must contain RETURN."
        )