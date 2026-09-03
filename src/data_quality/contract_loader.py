import re
from pathlib import Path
from typing import Any

import yaml


ALLOWED_COLUMN_TYPES = {
    "string",
    "float",
    "date",
    "datetime",
}


class ContractLoadError(ValueError):
    pass


def _validate_dataset_metadata(
    dataset: dict[str, Any],
    path: Path,
) -> None:
    dataset_format = dataset.get("format")

    if (
        dataset_format is not None
        and dataset_format != "csv"
    ):
        raise ContractLoadError(
            f"Unsupported dataset format in {path}: "
            f"{dataset_format}"
        )

    additional_columns = dataset.get(
        "additionalColumnsAllowed"
    )

    if (
        additional_columns is not None
        and not isinstance(additional_columns, bool)
    ):
        raise ContractLoadError(
            "dataset.additionalColumnsAllowed must be "
            f"a boolean in {path}"
        )

    kind = dataset.get("kind")

    if kind is not None and kind != "relationship":
        raise ContractLoadError(
            f"Unsupported dataset kind in {path}: {kind}"
        )

    if kind == "relationship":
        relationship_type = dataset.get(
            "relationshipType"
        )

        if (
            not isinstance(relationship_type, str)
            or not relationship_type
        ):
            raise ContractLoadError(
                "Relationship contract must define "
                f"dataset.relationshipType: {path}"
            )


def _validate_column_rules(
    columns: dict[str, Any],
    path: Path,
) -> None:
    for column_name, rules in columns.items():
        if not isinstance(rules, dict):
            raise ContractLoadError(
                f"Column '{column_name}' must contain "
                f"a mapping of rules: {path}"
            )

        column_type = rules.get("type")

        if column_type not in ALLOWED_COLUMN_TYPES:
            raise ContractLoadError(
                f"Column '{column_name}' uses unsupported "
                f"type '{column_type}': {path}"
            )

        for boolean_rule in ("required", "unique"):
            value = rules.get(boolean_rule)

            if (
                value is not None
                and not isinstance(value, bool)
            ):
                raise ContractLoadError(
                    f"Column '{column_name}' rule "
                    f"'{boolean_rule}' must be a boolean: "
                    f"{path}"
                )

        pattern = rules.get("pattern")

        if pattern is not None:
            if not isinstance(pattern, str):
                raise ContractLoadError(
                    f"Column '{column_name}' pattern must "
                    f"be a string: {path}"
                )

            try:
                re.compile(pattern)
            except re.error as exc:
                raise ContractLoadError(
                    f"Column '{column_name}' has invalid "
                    f"pattern: {exc}: {path}"
                ) from exc

        allowed_values = rules.get("allowedValues")

        if allowed_values is not None:
            if (
                not isinstance(allowed_values, list)
                or not allowed_values
            ):
                raise ContractLoadError(
                    f"Column '{column_name}' "
                    f"allowedValues must be a non-empty "
                    f"list: {path}"
                )

        minimum_length = rules.get("minimumLength")

        if minimum_length is not None:
            if (
                not isinstance(minimum_length, int)
                or isinstance(minimum_length, bool)
                or minimum_length < 0
            ):
                raise ContractLoadError(
                    f"Column '{column_name}' "
                    f"minimumLength must be a "
                    f"non-negative integer: {path}"
                )

        minimum = rules.get("minimum")

        if minimum is not None:
            if (
                not isinstance(minimum, (int, float))
                or isinstance(minimum, bool)
            ):
                raise ContractLoadError(
                    f"Column '{column_name}' minimum "
                    f"must be numeric: {path}"
                )

        if column_type in {"date", "datetime"}:
            value_format = rules.get("format")

            if not isinstance(value_format, str):
                raise ContractLoadError(
                    f"Column '{column_name}' must define "
                    f"a date/datetime format: {path}"
                )

        reference = rules.get("references")

        if reference is not None:
            if not isinstance(reference, dict):
                raise ContractLoadError(
                    f"Column '{column_name}' references "
                    f"must be a mapping: {path}"
                )

            referenced_dataset = reference.get("dataset")
            referenced_column = reference.get("column")

            if (
                not isinstance(referenced_dataset, str)
                or not referenced_dataset
                or not isinstance(referenced_column, str)
                or not referenced_column
            ):
                raise ContractLoadError(
                    f"Column '{column_name}' references "
                    f"must define dataset and column: {path}"
                )


def load_contract(
    contract_path: str | Path,
) -> dict[str, Any]:
    path = Path(contract_path)

    if not path.is_file():
        raise ContractLoadError(
            f"Contract file does not exist: {path}"
        )

    try:
        with path.open("r", encoding="utf-8") as file:
            contract = yaml.safe_load(file)
    except (OSError, yaml.YAMLError) as exc:
        raise ContractLoadError(
            f"Could not load contract {path}: {exc}"
        ) from exc

    if not isinstance(contract, dict):
        raise ContractLoadError(
            f"Contract must contain a YAML mapping: {path}"
        )

    if contract.get("contractVersion") != "1.0":
        raise ContractLoadError(
            f"Unsupported contractVersion in {path}"
        )

    dataset = contract.get("dataset")

    if not isinstance(dataset, dict):
        raise ContractLoadError(
            f"Missing or invalid dataset section in {path}"
        )

    dataset_name = dataset.get("name")
    dataset_path = dataset.get("path")

    if not isinstance(dataset_name, str) or not dataset_name:
        raise ContractLoadError(
            f"Missing dataset.name in {path}"
        )

    if not isinstance(dataset_path, str) or not dataset_path:
        raise ContractLoadError(
            f"Missing dataset.path in {path}"
        )

    _validate_dataset_metadata(dataset, path)

    columns = contract.get("columns")

    if not isinstance(columns, dict) or not columns:
        raise ContractLoadError(
            f"Missing or invalid columns section in {path}"
        )

    _validate_column_rules(columns, path)

    primary_key = contract.get("primaryKey")

    if not isinstance(primary_key, list) or not primary_key:
        raise ContractLoadError(
            f"Missing or invalid primaryKey in {path}"
        )

    if not all(
        isinstance(column, str) and column
        for column in primary_key
    ):
        raise ContractLoadError(
            f"Primary-key columns must be strings: {path}"
        )

    if len(primary_key) != len(set(primary_key)):
        raise ContractLoadError(
            f"Primary key contains duplicate columns: {path}"
        )

    for column_name in primary_key:
        if column_name not in columns:
            raise ContractLoadError(
                f"Primary-key column '{column_name}' is not "
                f"declared in columns: {path}"
            )

    return contract


def load_contracts(
    contracts_directory: str | Path,
) -> dict[str, dict[str, Any]]:
    directory = Path(contracts_directory)

    if not directory.is_dir():
        raise ContractLoadError(
            f"Contracts directory does not exist: {directory}"
        )

    contract_paths = sorted(directory.glob("*.yaml"))

    if not contract_paths:
        raise ContractLoadError(
            f"No YAML contracts found in: {directory}"
        )

    contracts: dict[str, dict[str, Any]] = {}

    for path in contract_paths:
        contract = load_contract(path)
        dataset_name = contract["dataset"]["name"]

        if dataset_name in contracts:
            raise ContractLoadError(
                f"Duplicate dataset contract: {dataset_name}"
            )

        contracts[dataset_name] = contract

    return contracts