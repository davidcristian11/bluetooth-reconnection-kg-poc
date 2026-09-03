import csv
from pathlib import Path
from typing import Any


def validate_dataset_structure(
    contract: dict[str, Any],
    project_root: str | Path,
) -> list[str]:
    root = Path(project_root)
    dataset = contract["dataset"]
    dataset_name = dataset["name"]
    csv_path = root / dataset["path"]

    issues: list[str] = []

    if not csv_path.is_file():
        return [
            f"{dataset_name}: dataset file does not exist: "
            f"{csv_path}"
        ]

    try:
        with csv_path.open(
            "r",
            encoding=dataset.get("encoding", "utf-8"),
            newline="",
        ) as file:
            reader = csv.reader(
                file,
                delimiter=dataset.get("delimiter", ","),
            )
            header = next(reader, None)
    except (OSError, UnicodeError, csv.Error) as exc:
        return [
            f"{dataset_name}: could not read dataset: {exc}"
        ]

    if header is None:
        return [f"{dataset_name}: dataset is empty"]

    if not header:
        return [f"{dataset_name}: dataset header is empty"]

    duplicate_columns = sorted(
        {
            column
            for column in header
            if header.count(column) > 1
        }
    )

    if duplicate_columns:
        issues.append(
            f"{dataset_name}: duplicate columns: "
            f"{duplicate_columns}"
        )

    declared_columns = set(contract["columns"])
    actual_columns = set(header)

    missing_columns = sorted(
        declared_columns - actual_columns
    )

    if missing_columns:
        issues.append(
            f"{dataset_name}: missing columns: "
            f"{missing_columns}"
        )

    additional_columns_allowed = dataset.get(
        "additionalColumnsAllowed",
        False,
    )

    if not additional_columns_allowed:
        unexpected_columns = sorted(
            actual_columns - declared_columns
        )

        if unexpected_columns:
            issues.append(
                f"{dataset_name}: unexpected columns: "
                f"{unexpected_columns}"
            )

    return issues


def validate_all_dataset_structures(
    contracts: dict[str, dict[str, Any]],
    project_root: str | Path,
) -> list[str]:
    issues: list[str] = []

    for dataset_name, contract in contracts.items():
        dataset_issues = validate_dataset_structure(
            contract,
            project_root,
        )

        issues.extend(dataset_issues)

    return issues