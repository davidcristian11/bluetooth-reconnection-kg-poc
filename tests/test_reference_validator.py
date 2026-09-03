from data_quality.reference_validator import (
    validate_references,
)


def make_contracts() -> dict:
    return {
        "requirements": {
            "dataset": {
                "name": "requirements",
                "path": "data/requirements.csv",
            },
            "columns": {
                "id": {
                    "type": "string",
                },
            },
        },
        "test_verifies_requirement": {
            "dataset": {
                "name": "test_verifies_requirement",
                "path": "data/test_verifies_requirement.csv",
            },
            "columns": {
                "testId": {
                    "type": "string",
                },
                "requirementId": {
                    "type": "string",
                    "references": {
                        "dataset": "requirements",
                        "column": "id",
                    },
                },
            },
        },
    }


def write_datasets(
    tmp_path,
    relationship_requirement_id: str,
):
    data_directory = tmp_path / "data"
    data_directory.mkdir()

    (data_directory / "requirements.csv").write_text(
        "id\nREQ-001\n",
        encoding="utf-8",
    )

    (
        data_directory
        / "test_verifies_requirement.csv"
    ).write_text(
        "testId,requirementId\n"
        f"TEST-001,{relationship_requirement_id}\n",
        encoding="utf-8",
    )


def test_accepts_valid_reference(tmp_path):
    write_datasets(tmp_path, "REQ-001")

    issues = validate_references(
        make_contracts(),
        tmp_path,
    )

    assert issues == []


def test_detects_orphan_reference(tmp_path):
    write_datasets(tmp_path, "REQ-999")

    issues = validate_references(
        make_contracts(),
        tmp_path,
    )

    assert any(
        "does not exist in requirements.id" in issue
        for issue in issues
    )


def test_detects_unknown_referenced_dataset(tmp_path):
    write_datasets(tmp_path, "REQ-001")
    contracts = make_contracts()

    reference = contracts[
        "test_verifies_requirement"
    ]["columns"]["requirementId"]["references"]

    reference["dataset"] = "unknown_dataset"

    issues = validate_references(
        contracts,
        tmp_path,
    )

    assert any(
        "referenced dataset" in issue
        for issue in issues
    )