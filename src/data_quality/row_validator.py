import csv
import re
from datetime import date, datetime
from pathlib import Path
from typing import Any


def _validate_value(
    value: str,
    rules: dict[str, Any],
) -> list[str]:
    issues: list[str] = []
    expected_type = rules.get("type", "string")
    parsed_value: Any = value
    type_is_valid = True

    if expected_type == "float":
        try:
            parsed_value = float(value)
        except ValueError:
            type_is_valid = False
            issues.append("must be a valid float")

    elif expected_type in {"date", "datetime"}:
        value_format = rules.get("format")

        if not isinstance(value_format, str):
            type_is_valid = False
            issues.append(
                f"{expected_type} format is not configured"
            )
        else:
            try:
                parsed_value = datetime.strptime(
                    value,
                    value_format,
                )
            except ValueError:
                type_is_valid = False
                issues.append(
                    f"must match format {value_format}"
                )

    elif expected_type != "string":
        type_is_valid = False
        issues.append(
            f"uses unsupported type '{expected_type}'"
        )

    pattern = rules.get("pattern")

    if pattern and re.fullmatch(pattern, value) is None:
        issues.append(
            f"does not match pattern {pattern}"
        )

    allowed_values = rules.get("allowedValues")

    if (
        isinstance(allowed_values, list)
        and value not in allowed_values
    ):
        issues.append(
            f"must be one of {allowed_values}"
        )

    minimum_length = rules.get("minimumLength")

    if (
        isinstance(minimum_length, int)
        and len(value) < minimum_length
    ):
        issues.append(
            f"must contain at least {minimum_length} characters"
        )

    minimum = rules.get("minimum")

    if (
        expected_type == "float"
        and type_is_valid
        and minimum is not None
        and parsed_value < minimum
    ):
        issues.append(
            f"must be greater than or equal to {minimum}"
        )

    if (
        rules.get("notFuture") is True
        and type_is_valid
        and expected_type in {"date", "datetime"}
        and parsed_value.date() > date.today()
    ):
        issues.append("must not be in the future")

    return issues


def validate_dataset_rows(
    contract: dict[str, Any],
    project_root: str | Path,
) -> list[str]:
    root = Path(project_root)
    dataset = contract["dataset"]
    dataset_name = dataset["name"]
    csv_path = root / dataset["path"]
    columns = contract["columns"]
    primary_key = contract["primaryKey"]

    issues: list[str] = []
    seen_primary_keys: set[tuple[str, ...]] = set()

    unique_values: dict[str, set[str]] = {
        column_name: set()
        for column_name, rules in columns.items()
        if rules.get("unique") is True
    }

    try:
        with csv_path.open(
            "r",
            encoding=dataset.get("encoding", "utf-8"),
            newline="",
        ) as file:
            reader = csv.DictReader(
                file,
                delimiter=dataset.get("delimiter", ","),
            )

            for row_number, row in enumerate(reader, start=2):
                normalized_row = {
                    column: (
                        value.strip()
                        if isinstance(value, str)
                        else ""
                    )
                    for column, value in row.items()
                    if column is not None
                }

                for column_name, rules in columns.items():
                    value = normalized_row.get(
                        column_name,
                        "",
                    )

                    if not value:
                        if rules.get("required") is True:
                            issues.append(
                                f"{dataset_name} row "
                                f"{row_number}, column "
                                f"'{column_name}': "
                                f"value is required"
                            )
                        continue

                    value_issues = _validate_value(
                        value,
                        rules,
                    )

                    for message in value_issues:
                        issues.append(
                            f"{dataset_name} row "
                            f"{row_number}, column "
                            f"'{column_name}': {message}"
                        )

                    if column_name in unique_values:
                        seen_values = unique_values[column_name]

                        if value in seen_values:
                            issues.append(
                                f"{dataset_name} row "
                                f"{row_number}, column "
                                f"'{column_name}': "
                                f"duplicate value '{value}'"
                            )
                        else:
                            seen_values.add(value)

                key = tuple(
                    normalized_row.get(column, "")
                    for column in primary_key
                )

                if all(key):
                    if key in seen_primary_keys:
                        issues.append(
                            f"{dataset_name} row "
                            f"{row_number}: duplicate "
                            f"primary key {key}"
                        )
                    else:
                        seen_primary_keys.add(key)

    except (OSError, UnicodeError, csv.Error) as exc:
        issues.append(
            f"{dataset_name}: could not validate rows: {exc}"
        )

    return issues


def validate_all_dataset_rows(
    contracts: dict[str, dict[str, Any]],
    project_root: str | Path,
) -> list[str]:
    issues: list[str] = []

    for contract in contracts.values():
        issues.extend(
            validate_dataset_rows(
                contract,
                project_root,
            )
        )

    return issues