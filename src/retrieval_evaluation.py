from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass
import math
import re

from flat_retriever import FlatSearchResult


ENTITY_ID_PATTERN = re.compile(
    r"^(FEAT|REQ|COMP|TEST|EXEC|TRACE|DEF)-\d+$",
    flags=re.IGNORECASE,
)

SOURCE_SYSTEM_VALUES = {
    "ProductDefinitionSystem",
    "RequirementsSystem",
    "SoftwareArchitectureSystem",
    "TestManagementSystem",
    "TraceRepository",
    "DefectTrackingSystem",
}

ENVIRONMENT_VALUES = {
    "SiL",
    "HiL",
    "Vehicle",
}

RESULT_VALUES = {
    "PASS",
    "FAIL",
}


@dataclass(frozen=True)
class RetrievalMetrics:
    recall: float
    precision: float
    evidence_complete: bool
    expected_atoms: tuple[str, ...]
    matched_atoms: tuple[str, ...]
    missing_atoms: tuple[str, ...]
    unexpected_atoms: tuple[str, ...]


def flat_results_to_records(
    results: list[FlatSearchResult],
) -> list[dict]:
    return [
        {
            "documentId": result.document.document_id,
            "kind": result.document.kind,
            "text": result.document.text,
            "metadata": result.document.metadata,
            "score": result.score,
        }
        for result in results
    ]


def _flatten_values(value) -> list:
    if isinstance(value, Mapping):
        flattened = []

        for nested in value.values():
            flattened.extend(
                _flatten_values(nested)
            )

        return flattened

    if isinstance(value, (list, tuple, set)):
        flattened = []

        for nested in value:
            flattened.extend(
                _flatten_values(nested)
            )

        return flattened

    return [value]


def _iter_mappings(value):
    if isinstance(value, Mapping):
        yield value

        for nested in value.values():
            yield from _iter_mappings(nested)

    elif isinstance(value, (list, tuple, set)):
        for nested in value:
            yield from _iter_mappings(nested)


def _normalize_number(value) -> str:
    number = float(value)

    if number.is_integer():
        return str(int(number))

    return format(number, ".12g")


def _is_number(value) -> bool:
    if isinstance(value, bool):
        return False

    if isinstance(value, (int, float)):
        return True

    if not isinstance(value, str):
        return False

    try:
        float(value)
    except ValueError:
        return False

    return True


def _normalized_entity_id(
    value,
) -> str | None:
    if not isinstance(value, str):
        return None

    candidate = value.strip()

    if ENTITY_ID_PATTERN.fullmatch(
        candidate
    ) is None:
        return None

    return candidate.upper()


def _canonical_choice(
    value,
    choices: set[str],
) -> str | None:
    if not isinstance(value, str):
        return None

    for choice in choices:
        if value.casefold() == choice.casefold():
            return choice

    return None


def _classify_expected_value(value) -> str:
    entity_id = _normalized_entity_id(value)

    if entity_id is not None:
        return f"id:{entity_id}"

    source_system = _canonical_choice(
        value,
        SOURCE_SYSTEM_VALUES,
    )

    if source_system is not None:
        return (
            f"source_system:{source_system}"
        )

    environment = _canonical_choice(
        value,
        ENVIRONMENT_VALUES,
    )

    if environment is not None:
        return f"environment:{environment}"

    result = _canonical_choice(
        value,
        RESULT_VALUES,
    )

    if result is not None:
        return f"result:{result}"

    if _is_number(value):
        return (
            f"number:{_normalize_number(value)}"
        )

    return (
        f"literal:{str(value).casefold()}"
    )


def build_expected_atoms(
    expected: dict,
) -> set[str]:
    atoms = {
        _classify_expected_value(value)
        for value in expected.get(
            "required_values",
            [],
        )
    }

    for expected_ids in expected.get(
        "exact_id_sets",
        {},
    ).values():
        atoms.update(
            f"id:{str(entity_id).upper()}"
            for entity_id in expected_ids
        )

    for environment, counts in expected.get(
        "environment_result_counts",
        {},
    ).items():
        for result, count in counts.items():
            atoms.add(
                f"count:{environment}:"
                f"{result}:{int(count)}"
            )

    return atoms


def _find_key(
    mapping: Mapping,
    fragment: str,
):
    fragment = fragment.casefold()

    for key in mapping:
        if fragment in str(key).casefold():
            return key

    return None


def _extract_count_atoms(
    records: list[dict],
) -> set[str]:
    direct_atoms = set()
    raw_counts = Counter()
    seen_execution_ids = set()

    for mapping in _iter_mappings(records):
        environment_key = _find_key(
            mapping,
            "environment",
        )

        if environment_key is None:
            continue

        environment = _canonical_choice(
            mapping[environment_key],
            ENVIRONMENT_VALUES,
        )

        if environment is None:
            continue

        pass_key = _find_key(
            mapping,
            "pass",
        )

        fail_key = _find_key(
            mapping,
            "fail",
        )

        if (
            pass_key is not None
            and _is_number(
                mapping[pass_key]
            )
        ):
            direct_atoms.add(
                f"count:{environment}:PASS:"
                f"{int(float(mapping[pass_key]))}"
            )

        if (
            fail_key is not None
            and _is_number(
                mapping[fail_key]
            )
        ):
            direct_atoms.add(
                f"count:{environment}:FAIL:"
                f"{int(float(mapping[fail_key]))}"
            )

        result_key = _find_key(
            mapping,
            "result",
        )

        if result_key is None:
            continue

        result = _canonical_choice(
            mapping[result_key],
            RESULT_VALUES,
        )

        if result is None:
            continue

        count_key = _find_key(
            mapping,
            "count",
        )

        if (
            count_key is not None
            and _is_number(
                mapping[count_key]
            )
        ):
            direct_atoms.add(
                f"count:{environment}:"
                f"{result}:"
                f"{int(float(mapping[count_key]))}"
            )
            continue

        execution_ids = {
            entity_id
            for value in _flatten_values(
                mapping
            )
            if (
                entity_id
                := _normalized_entity_id(
                    value
                )
            )
            and entity_id.startswith(
                "EXEC-"
            )
        }

        if execution_ids:
            new_execution_ids = (
                execution_ids
                - seen_execution_ids
            )

            for execution_id in (
                new_execution_ids
            ):
                raw_counts[
                    (environment, result)
                ] += 1

                seen_execution_ids.add(
                    execution_id
                )

        else:
            raw_counts[
                (environment, result)
            ] += 1

    if direct_atoms:
        return direct_atoms

    return {
        f"count:{environment}:"
        f"{result}:{count}"
        for (
            environment,
            result,
        ), count in raw_counts.items()
    }


def extract_candidate_atoms(
    records: list[dict],
    expected: dict,
) -> set[str]:
    flattened = _flatten_values(records)

    expected_atoms = build_expected_atoms(
        expected
    )

    actual_atoms = set()

    expected_prefixes = {
        atom.split(
            ":",
            1,
        )[1].split(
            "-",
            1,
        )[0]
        for atom in expected_atoms
        if atom.startswith("id:")
    }

    for value in flattened:
        entity_id = _normalized_entity_id(
            value
        )

        if entity_id is None:
            continue

        prefix = entity_id.split(
            "-",
            1,
        )[0]

        if prefix in expected_prefixes:
            actual_atoms.add(
                f"id:{entity_id}"
            )

    if any(
        atom.startswith(
            "source_system:"
        )
        for atom in expected_atoms
    ):
        for value in flattened:
            source_system = (
                _canonical_choice(
                    value,
                    SOURCE_SYSTEM_VALUES,
                )
            )

            if source_system is not None:
                actual_atoms.add(
                    "source_system:"
                    f"{source_system}"
                )

    if any(
        atom.startswith(
            "environment:"
        )
        for atom in expected_atoms
    ):
        for value in flattened:
            environment = _canonical_choice(
                value,
                ENVIRONMENT_VALUES,
            )

            if environment is not None:
                actual_atoms.add(
                    f"environment:"
                    f"{environment}"
                )

    if any(
        atom.startswith("result:")
        for atom in expected_atoms
    ):
        for value in flattened:
            result = _canonical_choice(
                value,
                RESULT_VALUES,
            )

            if result is not None:
                actual_atoms.add(
                    f"result:{result}"
                )

    for atom in expected_atoms:
        if atom.startswith("number:"):
            expected_number = atom.split(
                ":",
                1,
            )[1]

            if any(
                _is_number(value)
                and _normalize_number(
                    value
                )
                == expected_number
                for value in flattened
            ):
                actual_atoms.add(atom)

        if atom.startswith("literal:"):
            expected_literal = atom.split(
                ":",
                1,
            )[1]

            if any(
                isinstance(value, str)
                and value.casefold()
                == expected_literal
                for value in flattened
            ):
                actual_atoms.add(atom)

    if any(
        atom.startswith("count:")
        for atom in expected_atoms
    ):
        actual_atoms.update(
            _extract_count_atoms(
                records
            )
        )

    return actual_atoms


def evaluate_retrieved_evidence(
    records: list[dict],
    expected: dict,
) -> RetrievalMetrics:
    if expected.get("result") == "empty":
        correct = not records
        score = (
            1.0
            if correct
            else 0.0
        )

        return RetrievalMetrics(
            recall=score,
            precision=score,
            evidence_complete=correct,
            expected_atoms=tuple(),
            matched_atoms=tuple(),
            missing_atoms=tuple(),
            unexpected_atoms=tuple(),
        )

    expected_atoms = build_expected_atoms(
        expected
    )

    actual_atoms = extract_candidate_atoms(
        records,
        expected,
    )

    matched = (
        expected_atoms
        & actual_atoms
    )

    missing = (
        expected_atoms
        - actual_atoms
    )

    unexpected = (
        actual_atoms
        - expected_atoms
    )

    recall = (
        len(matched)
        / len(expected_atoms)
        if expected_atoms
        else (
            1.0
            if records
            else 0.0
        )
    )

    precision = (
        len(matched)
        / len(actual_atoms)
        if actual_atoms
        else 0.0
    )

    return RetrievalMetrics(
        recall=recall,
        precision=precision,
        evidence_complete=(
            bool(records)
            and math.isclose(
                recall,
                1.0,
            )
        ),
        expected_atoms=tuple(
            sorted(expected_atoms)
        ),
        matched_atoms=tuple(
            sorted(matched)
        ),
        missing_atoms=tuple(
            sorted(missing)
        ),
        unexpected_atoms=tuple(
            sorted(unexpected)
        ),
    )