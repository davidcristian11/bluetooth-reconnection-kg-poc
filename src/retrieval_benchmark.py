from dataclasses import dataclass
from pathlib import Path

import yaml


SUPPORTED_RETRIEVAL_CATEGORIES = {
    "direct_relationship",
    "one_to_many",
    "multi_hop",
    "cross_source",
    "cross_environment",
    "filtering",
    "aggregation",
}


class RetrievalBenchmarkDefinitionError(ValueError):
    pass


@dataclass(frozen=True)
class RetrievalBenchmarkCase:
    id: str
    category: str
    question: str
    top_k: int
    expected: dict


def _validate_positive_int(
    value,
    field_name: str,
) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise RetrievalBenchmarkDefinitionError(
            f"{field_name} must be a positive integer."
        )

    return value


def load_retrieval_benchmark(
    path: Path,
) -> tuple[int, list[RetrievalBenchmarkCase]]:
    if not path.is_file():
        raise RetrievalBenchmarkDefinitionError(
            f"Retrieval benchmark file does not exist: {path}"
        )

    with path.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file)

    if not isinstance(data, dict):
        raise RetrievalBenchmarkDefinitionError(
            "Retrieval benchmark root must be a YAML mapping."
        )

    version = data.get("version")
    raw_cases = data.get("cases")

    if not isinstance(version, int):
        raise RetrievalBenchmarkDefinitionError(
            "Retrieval benchmark version must be an integer."
        )

    default_top_k = _validate_positive_int(
        data.get("defaultTopK"),
        "defaultTopK",
    )

    if not isinstance(raw_cases, list) or not raw_cases:
        raise RetrievalBenchmarkDefinitionError(
            "Retrieval benchmark must contain at least one case."
        )

    cases = []
    seen_ids = set()

    for index, raw_case in enumerate(raw_cases, start=1):
        if not isinstance(raw_case, dict):
            raise RetrievalBenchmarkDefinitionError(
                f"Retrieval benchmark case #{index} must be a mapping."
            )

        case_id = raw_case.get("id")
        category = raw_case.get("category")
        question = raw_case.get("question")
        expected = raw_case.get("expected")

        if not isinstance(case_id, str) or not case_id.strip():
            raise RetrievalBenchmarkDefinitionError(
                f"Retrieval benchmark case #{index} has an invalid id."
            )

        if case_id in seen_ids:
            raise RetrievalBenchmarkDefinitionError(
                f"Duplicate retrieval benchmark case id: {case_id}"
            )

        if category not in SUPPORTED_RETRIEVAL_CATEGORIES:
            raise RetrievalBenchmarkDefinitionError(
                f"Unsupported retrieval category for {case_id}: "
                f"{category!r}"
            )

        if not isinstance(question, str) or not question.strip():
            raise RetrievalBenchmarkDefinitionError(
                f"Retrieval benchmark case {case_id} has an invalid question."
            )

        if not isinstance(expected, dict):
            raise RetrievalBenchmarkDefinitionError(
                f"Retrieval benchmark case {case_id} has invalid expected data."
            )

        if expected.get("result") not in {"empty", "non_empty"}:
            raise RetrievalBenchmarkDefinitionError(
                f"Retrieval benchmark case {case_id} must define "
                "expected.result as 'empty' or 'non_empty'."
            )

        top_k = _validate_positive_int(
            raw_case.get("topK", default_top_k),
            f"topK for {case_id}",
        )

        seen_ids.add(case_id)
        cases.append(
            RetrievalBenchmarkCase(
                id=case_id,
                category=category,
                question=question.strip(),
                top_k=top_k,
                expected=expected,
            )
        )

    return version, cases