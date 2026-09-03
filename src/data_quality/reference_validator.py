import csv
from pathlib import Path
from typing import Any


def load_rows(
    contract: dict[str, Any],
    project_root: Path,
) -> list[dict[str, str]]:
    dataset = contract["dataset"]
    csv_path = project_root / dataset["path"]

    with csv_path.open(
        "r",
        encoding=dataset.get("encoding", "utf-8"),
        newline="",
    ) as file:
        reader = csv.DictReader(
            file,
            delimiter=dataset.get("delimiter", ","),
        )

        return [
            {
                column: value.strip()
                for column, value in row.items()
                if column is not None
                and isinstance(value, str)
            }
            for row in reader
        ]


def validate_references(
    contracts: dict[str, dict[str, Any]],
    project_root: str | Path,
) -> list[str]:
    root = Path(project_root)
    issues: list[str] = []
    rows_by_dataset: dict[
        str,
        list[dict[str, str]],
    ] = {}

    for dataset_name, contract in contracts.items():
        try:
            rows_by_dataset[dataset_name] = load_rows(
                contract,
                root,
            )
        except (OSError, UnicodeError, csv.Error) as exc:
            issues.append(
                f"{dataset_name}: could not read dataset "
                f"for reference validation: {exc}"
            )

    if issues:
        return issues

    for dataset_name, contract in contracts.items():
        source_rows = rows_by_dataset[dataset_name]

        for column_name, rules in contract["columns"].items():
            reference = rules.get("references")

            if not isinstance(reference, dict):
                continue

            target_dataset = reference.get("dataset")
            target_column = reference.get("column")

            if target_dataset not in contracts:
                issues.append(
                    f"{dataset_name}, column "
                    f"'{column_name}': referenced dataset "
                    f"'{target_dataset}' does not exist"
                )
                continue

            target_contract = contracts[target_dataset]

            if target_column not in target_contract["columns"]:
                issues.append(
                    f"{dataset_name}, column "
                    f"'{column_name}': referenced column "
                    f"'{target_column}' does not exist in "
                    f"dataset '{target_dataset}'"
                )
                continue

            target_values = {
                row.get(target_column, "")
                for row in rows_by_dataset[target_dataset]
            }

            for row_number, row in enumerate(
                source_rows,
                start=2,
            ):
                source_value = row.get(column_name, "")

                if not source_value:
                    continue

                if source_value not in target_values:
                    issues.append(
                        f"{dataset_name} row {row_number}, "
                        f"column '{column_name}': value "
                        f"'{source_value}' does not exist in "
                        f"{target_dataset}.{target_column}"
                    )

    return issues