import pytest

from data_quality.contract_loader import (
    ContractLoadError,
    load_contract,
    load_contracts,
)


VALID_CONTRACT = """
contractVersion: "1.0"

dataset:
  name: requirements
  path: data/nodes/requirements.csv

primaryKey:
  - id

columns:
  id:
    type: string
    required: true
"""


def test_load_valid_contract(tmp_path):
    path = tmp_path / "requirements.yaml"
    path.write_text(VALID_CONTRACT, encoding="utf-8")

    contract = load_contract(path)

    assert contract["dataset"]["name"] == "requirements"
    assert contract["primaryKey"] == ["id"]


def test_rejects_invalid_yaml(tmp_path):
    path = tmp_path / "invalid.yaml"
    path.write_text("dataset: [", encoding="utf-8")

    with pytest.raises(ContractLoadError):
        load_contract(path)


def test_rejects_missing_primary_key(tmp_path):
    path = tmp_path / "invalid.yaml"
    path.write_text(
        """
contractVersion: "1.0"

dataset:
  name: requirements
  path: data/nodes/requirements.csv

columns:
  id:
    type: string
""",
        encoding="utf-8",
    )

    with pytest.raises(ContractLoadError):
        load_contract(path)


def test_rejects_duplicate_dataset_contracts(tmp_path):
    first = tmp_path / "first.yaml"
    second = tmp_path / "second.yaml"

    first.write_text(VALID_CONTRACT, encoding="utf-8")
    second.write_text(VALID_CONTRACT, encoding="utf-8")

    with pytest.raises(
        ContractLoadError,
        match="Duplicate dataset contract",
    ):
        load_contracts(tmp_path)


def test_rejects_unsupported_column_type(tmp_path):
    path = tmp_path / "invalid.yaml"
    content = VALID_CONTRACT.replace(
        "type: string",
        "type: integer",
    )
    path.write_text(content, encoding="utf-8")

    with pytest.raises(
        ContractLoadError,
        match="unsupported type",
    ):
        load_contract(path)


def test_rejects_invalid_pattern(tmp_path):
    path = tmp_path / "invalid.yaml"
    content = VALID_CONTRACT.replace(
        "required: true",
        'required: true\n    pattern: "["',
    )
    path.write_text(content, encoding="utf-8")

    with pytest.raises(
        ContractLoadError,
        match="invalid pattern",
    ):
        load_contract(path)


def test_rejects_incomplete_reference(tmp_path):
    path = tmp_path / "invalid.yaml"
    content = VALID_CONTRACT.replace(
        "required: true",
        (
            "required: true\n"
            "    references:\n"
            "      dataset: requirements"
        ),
    )
    path.write_text(content, encoding="utf-8")

    with pytest.raises(
        ContractLoadError,
        match="must define dataset and column",
    ):
        load_contract(path)


def test_rejects_relationship_without_type(tmp_path):
    path = tmp_path / "invalid.yaml"
    content = VALID_CONTRACT.replace(
        "path: data/nodes/requirements.csv",
        (
            "path: data/nodes/requirements.csv\n"
            "  kind: relationship"
        ),
    )
    path.write_text(content, encoding="utf-8")

    with pytest.raises(
        ContractLoadError,
        match="relationshipType",
    ):
        load_contract(path)