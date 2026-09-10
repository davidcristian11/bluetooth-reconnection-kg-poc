from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
import json
import re

import yaml


SUPPORTED_CATEGORIES = {
    "entity_lookup",
    "relationship_traversal",
    "multi_hop_reasoning",
    "aggregation_filtering",
    "no_result_handling",
}

NO_RESULT_ANSWER_PHRASE = "no matching graph facts"


class BenchmarkDefinitionError(ValueError):
    pass


@dataclass(frozen=True)
class BenchmarkCase:
    id: str
    category: str
    question: str
    expected: dict


@dataclass
class EvaluationResult:
    case_id: str
    category: str
    question: str
    execution_success: bool
    retrieval_correct: bool
    answer_correct: bool
    generation_attempts: int | None
    cypher: str | None
    records: list[dict]
    answer: str | None
    retrieval_issues: list[str]
    answer_issues: list[str]
    error: str | None

    def to_dict(self) -> dict:
        return {
            "case_id": self.case_id,
            "category": self.category,
            "question": self.question,
            "execution_success": self.execution_success,
            "retrieval_correct": self.retrieval_correct,
            "answer_correct": self.answer_correct,
            "outcome": classify_result(self),
            "generation_attempts": self.generation_attempts,
            "cypher": self.cypher,
            "records": self.records,
            "answer": self.answer,
            "retrieval_issues": self.retrieval_issues,
            "answer_issues": self.answer_issues,
            "error": self.error,
        }


def classify_result(
    result: EvaluationResult,
) -> str:
    if not result.execution_success:
        return "execution_failure"

    if not result.retrieval_correct:
        return "retrieval_failure"

    if not result.answer_correct:
        return "answer_failure"

    return "fully_correct"


def load_benchmark(
    path: Path,
) -> tuple[int, list[BenchmarkCase]]:
    if not path.is_file():
        raise BenchmarkDefinitionError(
            f"Benchmark file does not exist: {path}"
        )

    with path.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file)

    if not isinstance(data, dict):
        raise BenchmarkDefinitionError(
            "Benchmark root must be a YAML mapping."
        )

    version = data.get("version")
    raw_cases = data.get("cases")

    if not isinstance(version, int):
        raise BenchmarkDefinitionError(
            "Benchmark version must be an integer."
        )

    if not isinstance(raw_cases, list) or not raw_cases:
        raise BenchmarkDefinitionError(
            "Benchmark must contain at least one case."
        )

    cases = []
    seen_ids = set()

    for index, raw_case in enumerate(
        raw_cases,
        start=1,
    ):
        if not isinstance(raw_case, dict):
            raise BenchmarkDefinitionError(
                f"Benchmark case #{index} must be a mapping."
            )

        case_id = raw_case.get("id")
        category = raw_case.get("category")
        question = raw_case.get("question")
        expected = raw_case.get("expected")

        if not isinstance(case_id, str) or not case_id.strip():
            raise BenchmarkDefinitionError(
                f"Benchmark case #{index} has an invalid id."
            )

        if case_id in seen_ids:
            raise BenchmarkDefinitionError(
                f"Duplicate benchmark case id: {case_id}"
            )

        if category not in SUPPORTED_CATEGORIES:
            raise BenchmarkDefinitionError(
                f"Unsupported category for {case_id}: "
                f"{category!r}"
            )

        if not isinstance(question, str) or not question.strip():
            raise BenchmarkDefinitionError(
                f"Benchmark case {case_id} has an invalid question."
            )

        if not isinstance(expected, dict):
            raise BenchmarkDefinitionError(
                f"Benchmark case {case_id} has invalid expected data."
            )

        if expected.get("result") not in {
            "empty",
            "non_empty",
        }:
            raise BenchmarkDefinitionError(
                f"Benchmark case {case_id} must define "
                "expected.result as 'empty' or 'non_empty'."
            )

        seen_ids.add(case_id)

        cases.append(
            BenchmarkCase(
                id=case_id,
                category=category,
                question=question.strip(),
                expected=expected,
            )
        )

    return version, cases


def _flatten_values(value) -> list:
    if isinstance(value, Mapping):
        flattened = []

        for nested_value in value.values():
            flattened.extend(
                _flatten_values(nested_value)
            )

        return flattened

    if isinstance(value, (list, tuple, set)):
        flattened = []

        for nested_value in value:
            flattened.extend(
                _flatten_values(nested_value)
            )

        return flattened

    return [value]


def _values_match(
    actual,
    expected,
) -> bool:
    if isinstance(expected, bool):
        return actual is expected

    if isinstance(expected, (int, float)):
        if isinstance(actual, (int, float)):
            return float(actual) == float(expected)

        if isinstance(actual, str):
            numbers = re.findall(
                r"(?<![\w.-])-?\d+(?:\.\d+)?(?![\w.-])",
                actual,
            )

            return any(
                float(number) == float(expected)
                for number in numbers
            )

        return False

    return (
        str(actual).casefold()
        == str(expected).casefold()
    )


def _contains_value(
    values: list,
    expected,
) -> bool:
    return any(
        _values_match(actual, expected)
        for actual in values
    )


def _extract_ids(
    values: list,
    prefix: str,
) -> set[str]:
    pattern = re.compile(
        rf"\b{re.escape(prefix)}-\d+\b",
        flags=re.IGNORECASE,
    )

    found = set()

    for value in values:
        if not isinstance(value, str):
            continue

        found.update(
            match.upper()
            for match in pattern.findall(value)
        )

    return found


def _find_matching_key(
    record: Mapping,
    text: str,
):
    text = text.casefold()

    for key in record:
        if text in str(key).casefold():
            return key

    return None


def _validate_environment_result_counts(
    records: list[dict],
    expected_counts: dict,
) -> list[str]:
    issues = []

    for environment, result_counts in expected_counts.items():
        for result, expected_count in result_counts.items():
            matched = False

            for record in records:
                flattened = _flatten_values(record)

                if not _contains_value(
                    flattened,
                    environment,
                ):
                    continue

                # Shape 1:
                # environment | result | count
                if (
                    _contains_value(flattened, result)
                    and _contains_value(
                        flattened,
                        expected_count,
                    )
                ):
                    matched = True
                    break

                # Shape 2:
                # environment | passCount | failCount
                result_key = _find_matching_key(
                    record,
                    result,
                )

                if (
                    result_key is not None
                    and _values_match(
                        record[result_key],
                        expected_count,
                    )
                ):
                    matched = True
                    break

            if not matched:
                issues.append(
                    f"{environment} {result} count mismatch: "
                    f"expected {expected_count}"
                )

    return issues


def evaluate_retrieval(
    records: list[dict],
    expected: dict,
) -> tuple[bool, list[str]]:
    issues = []

    if expected["result"] == "empty":
        if records:
            issues.append(
                "expected an empty result but received "
                f"{len(records)} record(s)"
            )

        return not issues, issues

    if not records:
        return False, [
            "expected a non-empty result but received no records"
        ]

    flattened = _flatten_values(records)

    for required_value in expected.get(
        "required_values",
        [],
    ):
        if not _contains_value(
            flattened,
            required_value,
        ):
            issues.append(
                "retrieval is missing required value "
                f"{required_value!r}"
            )

    for prefix, expected_ids in expected.get(
        "exact_id_sets",
        {},
    ).items():
        expected_set = {
            str(value).upper()
            for value in expected_ids
        }

        actual_set = _extract_ids(
            flattened,
            prefix,
        )

        if actual_set != expected_set:
            issues.append(
                f"{prefix} id set mismatch: "
                f"expected {sorted(expected_set)}, "
                f"found {sorted(actual_set)}"
            )

    for group in expected.get(
        "required_record_value_groups",
        [],
    ):
        group_found = any(
            all(
                _contains_value(
                    _flatten_values(record),
                    expected_value,
                )
                for expected_value in group
            )
            for record in records
        )

        if not group_found:
            issues.append(
                "retrieval is missing expected record "
                f"value group {group!r}"
            )

    expected_counts = expected.get(
        "environment_result_counts"
    )

    if expected_counts:
        issues.extend(
            _validate_environment_result_counts(
                records,
                expected_counts,
            )
        )

    return not issues, issues


def _answer_contains_value(
    answer: str,
    expected,
) -> bool:
    if isinstance(expected, (int, float)):
        numbers = re.findall(
            r"(?<![\w.-])-?\d+(?:\.\d+)?(?![\w.-])",
            answer,
        )

        return any(
            float(number) == float(expected)
            for number in numbers
        )

    return (
        str(expected).casefold()
        in answer.casefold()
    )


def _extract_markdown_table_counts(
    answer: str,
) -> dict[str, dict[str, int | float]]:
    lines = [
        line.strip()
        for line in answer.splitlines()
        if line.strip().startswith("|")
    ]

    if len(lines) < 3:
        return {}

    headers = [
        value.strip().casefold()
        for value in lines[0].strip("|").split("|")
    ]

    environment_index = None
    pass_index = None
    fail_index = None

    for index, header in enumerate(headers):
        if "environment" in header:
            environment_index = index
        elif "pass" in header:
            pass_index = index
        elif "fail" in header:
            fail_index = index

    if (
        environment_index is None
        or pass_index is None
        or fail_index is None
    ):
        return {}

    parsed = {}

    for line in lines[2:]:
        cells = [
            value.strip()
            for value in line.strip("|").split("|")
        ]

        if len(cells) <= max(
            environment_index,
            pass_index,
            fail_index,
        ):
            continue

        environment = cells[environment_index]

        try:
            pass_count = float(cells[pass_index])
            fail_count = float(cells[fail_index])
        except ValueError:
            continue

        parsed[environment.casefold()] = {
            "PASS": pass_count,
            "FAIL": fail_count,
        }

    return parsed


def _validate_environment_counts_in_answer(
    answer: str,
    expected_counts: dict,
) -> list[str]:
    issues = []

    table_counts = _extract_markdown_table_counts(
        answer
    )

    for environment, result_counts in expected_counts.items():
        environment_key = environment.casefold()

        if environment_key in table_counts:
            actual_counts = table_counts[
                environment_key
            ]

            for result, expected_count in (
                result_counts.items()
            ):
                actual_count = actual_counts.get(result)

                if (
                    actual_count is None
                    or float(actual_count)
                    != float(expected_count)
                ):
                    issues.append(
                        f"answer has incorrect {result} "
                        f"count for {environment}: "
                        f"expected {expected_count}"
                    )

            continue

        environment_pattern = re.compile(
            re.escape(environment),
            flags=re.IGNORECASE,
        )

        match = environment_pattern.search(answer)

        if not match:
            issues.append(
                f"answer is missing environment "
                f"{environment!r}"
            )
            continue

        nearby_text = answer[
            match.start():
            match.start() + 300
        ]

        for result, expected_count in (
            result_counts.items()
        ):
            if result == "PASS":
                result_words = (
                    r"(?:pass|passed|passes)"
                )
            else:
                result_words = (
                    r"(?:fail|failed|failure|failures)"
                )

            forward_pattern = re.compile(
                rf"{result_words}"
                rf".{{0,40}}"
                rf"\b{re.escape(str(expected_count))}\b",
                flags=re.IGNORECASE | re.DOTALL,
            )

            reverse_pattern = re.compile(
                rf"\b{re.escape(str(expected_count))}\b"
                rf".{{0,40}}"
                rf"{result_words}",
                flags=re.IGNORECASE | re.DOTALL,
            )

            if not (
                forward_pattern.search(nearby_text)
                or reverse_pattern.search(nearby_text)
            ):
                issues.append(
                    f"answer is missing expected "
                    f"{result} count {expected_count} "
                    f"for {environment}"
                )

    return issues


def evaluate_answer(
    answer: str,
    expected: dict,
) -> tuple[bool, list[str]]:
    issues = []

    if expected["result"] == "empty":
        if (
            NO_RESULT_ANSWER_PHRASE
            not in answer.casefold()
        ):
            issues.append(
                "answer does not clearly state that no "
                "matching graph facts were retrieved"
            )

        return not issues, issues

    answer_values = list(
        expected.get(
            "required_values",
            [],
        )
    )

    if not answer_values:
        seen = set()

        for group in expected.get(
            "required_record_value_groups",
            [],
        ):
            for value in group:
                marker = (
                    type(value).__name__,
                    str(value).casefold(),
                )

                if marker not in seen:
                    seen.add(marker)
                    answer_values.append(value)

    for required_value in answer_values:
        if not _answer_contains_value(
            answer,
            required_value,
        ):
            issues.append(
                "answer is missing required value "
                f"{required_value!r}"
            )

    expected_counts = expected.get(
        "environment_result_counts"
    )

    if expected_counts:
        issues.extend(
            _validate_environment_counts_in_answer(
                answer,
                expected_counts,
            )
        )

    return not issues, issues


def build_summary(
    results: list[EvaluationResult],
) -> dict:
    total = len(results)

    outcomes = {
        "fully_correct": 0,
        "execution_failure": 0,
        "retrieval_failure": 0,
        "answer_failure": 0,
    }

    for result in results:
        outcomes[classify_result(result)] += 1

    category_summary = {}

    for category in sorted(
        {
            result.category
            for result in results
        }
    ):
        category_results = [
            result
            for result in results
            if result.category == category
        ]

        category_summary[category] = {
            "total": len(category_results),
            "execution_success": sum(
                result.execution_success
                for result in category_results
            ),
            "retrieval_correct": sum(
                result.retrieval_correct
                for result in category_results
            ),
            "answer_correct": sum(
                result.answer_correct
                for result in category_results
            ),
        }

    return {
        "total_cases": total,
        "execution_success": sum(
            result.execution_success
            for result in results
        ),
        "retrieval_correct": sum(
            result.retrieval_correct
            for result in results
        ),
        "answer_correct": sum(
            result.answer_correct
            for result in results
        ),
        "fully_correct": sum(
            result.execution_success
            and result.retrieval_correct
            and result.answer_correct
            for result in results
        ),
        "outcomes": outcomes,
        "by_category": category_summary,
    }


def write_results(
    path: Path,
    *,
    benchmark_version: int,
    configured_model: str,
    results: list[EvaluationResult],
) -> None:
    payload = {
        "benchmark_version": benchmark_version,
        "configured_model": configured_model,
        "summary": build_summary(results),
        "results": [
            result.to_dict()
            for result in results
        ],
    }

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        json.dumps(
            payload,
            indent=2,
            default=str,
        )
        + "\n",
        encoding="utf-8",
    )