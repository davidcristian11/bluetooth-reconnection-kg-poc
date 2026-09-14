from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path
import csv
import math
import re


PROJECT_ROOT = Path(__file__).resolve().parents[1]

NODE_DATASETS = {
    "Feature": "features.csv",
    "Requirement": "requirements.csv",
    "SoftwareComponent": "software_components.csv",
    "Test": "tests.csv",
    "TestExecution": "test_executions.csv",
    "TestTrace": "test_traces.csv",
    "DefectTicket": "defect_tickets.csv",
}

RELATIONSHIP_DATASETS = {
    "HAS_REQUIREMENT": (
        "feature_has_requirement.csv",
        "Feature",
        "featureId",
        "Requirement",
        "requirementId",
    ),
    "IMPLEMENTS": (
        "software_component_implements_requirement.csv",
        "SoftwareComponent",
        "componentId",
        "Requirement",
        "requirementId",
    ),
    "VERIFIES": (
        "test_verifies_requirement.csv",
        "Test",
        "testId",
        "Requirement",
        "requirementId",
    ),
    "EXECUTION_OF": (
        "test_execution_execution_of_test.csv",
        "TestExecution",
        "executionId",
        "Test",
        "testId",
    ),
    "PRODUCES": (
        "test_execution_produces_trace.csv",
        "TestExecution",
        "executionId",
        "TestTrace",
        "traceId",
    ),
    "HAS_DEFECT_TICKET": (
        "test_execution_has_defect_ticket.csv",
        "TestExecution",
        "executionId",
        "DefectTicket",
        "defectTicketId",
    ),
    "AFFECTS": (
        "defect_ticket_affects_component.csv",
        "DefectTicket",
        "defectTicketId",
        "SoftwareComponent",
        "componentId",
    ),
}

STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "did",
    "do",
    "does",
    "during",
    "for",
    "from",
    "how",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "this",
    "to",
    "was",
    "were",
    "what",
    "which",
    "with",
}

TOKEN_PATTERN = re.compile(
    r"[A-Za-z]+(?:-[0-9]+)?|[0-9]+(?:\.[0-9]+)?"
)

CAMEL_CASE_BOUNDARY = re.compile(
    r"(?<=[a-z0-9])(?=[A-Z])"
)

ENTITY_ID_PATTERN = re.compile(
    r"^[a-z]+-[0-9]+$",
    flags=re.IGNORECASE,
)


class FlatRetrievalError(ValueError):
    pass


@dataclass(frozen=True)
class FlatDocument:
    document_id: str
    kind: str
    text: str
    metadata: dict


@dataclass(frozen=True)
class FlatSearchResult:
    document: FlatDocument
    score: float


def _stem_token(token: str) -> str:
    normalized = token.casefold()

    if ENTITY_ID_PATTERN.fullmatch(normalized):
        return normalized

    if len(normalized) > 5 and normalized.endswith("ies"):
        return normalized[:-3] + "y"

    if len(normalized) > 5 and normalized.endswith("ing"):
        return normalized[:-3]

    if len(normalized) > 4 and normalized.endswith("ed"):
        return normalized[:-2]

    if len(normalized) > 4 and normalized.endswith("es"):
        return normalized[:-2]

    if len(normalized) > 3 and normalized.endswith("s"):
        return normalized[:-1]

    return normalized


def tokenize(text: str) -> list[str]:
    expanded = CAMEL_CASE_BOUNDARY.sub(
        " ",
        text.replace("_", " "),
    )

    tokens = []

    for raw_token in TOKEN_PATTERN.findall(expanded):
        token = _stem_token(raw_token)

        if token in STOP_WORDS or len(token) <= 1:
            continue

        tokens.append(token)

    return tokens


def _load_node_documents(
    project_root: Path,
) -> list[FlatDocument]:
    documents = []
    nodes_directory = project_root / "data" / "nodes"

    for label, filename in NODE_DATASETS.items():
        path = nodes_directory / filename

        with path.open(
            "r",
            encoding="utf-8",
            newline="",
        ) as file:
            for row in csv.DictReader(file):
                entity_id = row["id"]

                property_text = " ".join(
                    f"{name} {value}"
                    for name, value in row.items()
                    if value not in {None, ""}
                )

                documents.append(
                    FlatDocument(
                        document_id=(
                            f"node:{label}:{entity_id}"
                        ),
                        kind="node",
                        text=f"{label} {property_text}",
                        metadata={
                            "label": label,
                            **row,
                        },
                    )
                )

    return documents


def _load_relationship_documents(
    project_root: Path,
) -> list[FlatDocument]:
    documents = []
    relationships_directory = (
        project_root / "data" / "relationships"
    )

    for relationship_type, definition in (
        RELATIONSHIP_DATASETS.items()
    ):
        (
            filename,
            source_label,
            source_field,
            target_label,
            target_field,
        ) = definition

        path = relationships_directory / filename

        with path.open(
            "r",
            encoding="utf-8",
            newline="",
        ) as file:
            for row in csv.DictReader(file):
                source_id = row[source_field]
                target_id = row[target_field]

                documents.append(
                    FlatDocument(
                        document_id=(
                            "relationship:"
                            f"{relationship_type}:"
                            f"{source_id}:{target_id}"
                        ),
                        kind="relationship",
                        text=(
                            f"{source_label} {source_id} "
                            f"{relationship_type} "
                            f"{target_label} {target_id}"
                        ),
                        metadata={
                            "relationshipType": (
                                relationship_type
                            ),
                            "sourceLabel": source_label,
                            "sourceId": source_id,
                            "targetLabel": target_label,
                            "targetId": target_id,
                        },
                    )
                )

    return documents


def load_flat_documents(
    project_root: Path = PROJECT_ROOT,
) -> list[FlatDocument]:
    documents = _load_node_documents(project_root)
    documents.extend(
        _load_relationship_documents(project_root)
    )
    return documents


class LexicalFlatRetriever:
    def __init__(
        self,
        documents: list[FlatDocument],
        *,
        k1: float = 1.5,
        b: float = 0.75,
    ):
        if not documents:
            raise FlatRetrievalError(
                "Flat retriever requires at least one document."
            )

        self.documents = list(documents)
        self.k1 = k1
        self.b = b

        self._document_tokens = [
            tokenize(document.text)
            for document in self.documents
        ]

        self._term_frequencies = [
            Counter(tokens)
            for tokens in self._document_tokens
        ]

        self._document_lengths = [
            len(tokens)
            for tokens in self._document_tokens
        ]

        self._average_document_length = (
            sum(self._document_lengths)
            / len(self._document_lengths)
        )

        document_frequency = Counter()

        for tokens in self._document_tokens:
            document_frequency.update(set(tokens))

        document_count = len(self.documents)

        self._inverse_document_frequency = {
            token: math.log(
                1
                + (
                    document_count
                    - frequency
                    + 0.5
                )
                / (frequency + 0.5)
            )
            for token, frequency in (
                document_frequency.items()
            )
        }

    @classmethod
    def from_project_data(
        cls,
        project_root: Path = PROJECT_ROOT,
    ) -> "LexicalFlatRetriever":
        return cls(
            load_flat_documents(project_root)
        )

    def search(
        self,
        question: str,
        *,
        top_k: int,
    ) -> list[FlatSearchResult]:
        if isinstance(top_k, bool) or not isinstance(top_k, int):
            raise FlatRetrievalError(
                "top_k must be a positive integer."
            )

        if top_k <= 0:
            raise FlatRetrievalError(
                "top_k must be a positive integer."
            )

        query_tokens = tokenize(question)

        if not query_tokens:
            return []

        results = []

        for (
            document,
            term_frequency,
            document_length,
        ) in zip(
            self.documents,
            self._term_frequencies,
            self._document_lengths,
        ):
            score = 0.0

            for token in query_tokens:
                frequency = term_frequency.get(token, 0)

                if frequency == 0:
                    continue

                inverse_document_frequency = (
                    self._inverse_document_frequency.get(
                        token,
                        0.0,
                    )
                )

                denominator = (
                    frequency
                    + self.k1
                    * (
                        1
                        - self.b
                        + self.b
                        * document_length
                        / self._average_document_length
                    )
                )

                score += (
                    inverse_document_frequency
                    * frequency
                    * (self.k1 + 1)
                    / denominator
                )

            if score > 0:
                results.append(
                    FlatSearchResult(
                        document=document,
                        score=score,
                    )
                )

        results.sort(
            key=lambda result: (
                -result.score,
                result.document.document_id,
            )
        )

        return results[:top_k]