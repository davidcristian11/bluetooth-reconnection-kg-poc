from data_quality.dataset_validator import (
    validate_dataset_structure,
)


def make_contract() -> dict:
    return {
        "dataset": {
            "name": "requirements",
            "path": "data/requirements.csv",
            "encoding": "utf-8",
            "delimiter": ",",
            "additionalColumnsAllowed": False,
        },
        "columns": {
            "id": {"type": "string"},
            "title": {"type": "string"},
        },
    }


def test_accepts_valid_dataset_structure(tmp_path):
    data_directory = tmp_path / "data"
    data_directory.mkdir()

    csv_path = data_directory / "requirements.csv"
    csv_path.write_text(
        "id,title\nREQ-001,First requirement\n",
        encoding="utf-8",
    )

    issues = validate_dataset_structure(
        make_contract(),
        tmp_path,
    )

    assert issues == []


def test_detects_missing_column(tmp_path):
    data_directory = tmp_path / "data"
    data_directory.mkdir()

    csv_path = data_directory / "requirements.csv"
    csv_path.write_text(
        "id\nREQ-001\n",
        encoding="utf-8",
    )

    issues = validate_dataset_structure(
        make_contract(),
        tmp_path,
    )

    assert any("missing columns" in issue for issue in issues)


def test_detects_unexpected_column(tmp_path):
    data_directory = tmp_path / "data"
    data_directory.mkdir()

    csv_path = data_directory / "requirements.csv"
    csv_path.write_text(
        "id,title,extra\nREQ-001,Title,value\n",
        encoding="utf-8",
    )

    issues = validate_dataset_structure(
        make_contract(),
        tmp_path,
    )

    assert any(
        "unexpected columns" in issue
        for issue in issues
    )


def test_detects_missing_dataset_file(tmp_path):
    issues = validate_dataset_structure(
        make_contract(),
        tmp_path,
    )

    assert any(
        "does not exist" in issue
        for issue in issues
    )