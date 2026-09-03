from data_quality.row_validator import (
    validate_dataset_rows,
)


def make_contract() -> dict:
    return {
        "dataset": {
            "name": "executions",
            "path": "data/executions.csv",
            "encoding": "utf-8",
            "delimiter": ",",
        },
        "primaryKey": ["id"],
        "columns": {
            "id": {
                "type": "string",
                "required": True,
                "unique": True,
                "pattern": "^EXEC-[0-9]{3}$",
            },
            "result": {
                "type": "string",
                "required": True,
                "allowedValues": ["PASS", "FAIL"],
            },
            "duration": {
                "type": "float",
                "required": False,
                "minimum": 0,
            },
            "executionDate": {
                "type": "date",
                "required": True,
                "format": "%Y-%m-%d",
                "notFuture": True,
            },
        },
    }


def write_dataset(tmp_path, content):
    data_directory = tmp_path / "data"
    data_directory.mkdir()
    path = data_directory / "executions.csv"
    path.write_text(content, encoding="utf-8")


def test_accepts_valid_rows(tmp_path):
    write_dataset(
        tmp_path,
        "id,result,duration,executionDate\n"
        "EXEC-001,PASS,5.2,2026-01-01\n",
    )

    issues = validate_dataset_rows(
        make_contract(),
        tmp_path,
    )

    assert issues == []


def test_detects_missing_required_value(tmp_path):
    write_dataset(
        tmp_path,
        "id,result,duration,executionDate\n"
        "EXEC-001,,5.2,2026-01-01\n",
    )

    issues = validate_dataset_rows(
        make_contract(),
        tmp_path,
    )

    assert any("value is required" in issue for issue in issues)


def test_detects_invalid_pattern(tmp_path):
    write_dataset(
        tmp_path,
        "id,result,duration,executionDate\n"
        "INVALID,PASS,5.2,2026-01-01\n",
    )

    issues = validate_dataset_rows(
        make_contract(),
        tmp_path,
    )

    assert any("does not match pattern" in issue for issue in issues)


def test_detects_invalid_allowed_value(tmp_path):
    write_dataset(
        tmp_path,
        "id,result,duration,executionDate\n"
        "EXEC-001,UNKNOWN,5.2,2026-01-01\n",
    )

    issues = validate_dataset_rows(
        make_contract(),
        tmp_path,
    )

    assert any("must be one of" in issue for issue in issues)


def test_detects_negative_float(tmp_path):
    write_dataset(
        tmp_path,
        "id,result,duration,executionDate\n"
        "EXEC-001,FAIL,-1,2026-01-01\n",
    )

    issues = validate_dataset_rows(
        make_contract(),
        tmp_path,
    )

    assert any(
        "greater than or equal to" in issue
        for issue in issues
    )


def test_detects_duplicate_primary_key(tmp_path):
    write_dataset(
        tmp_path,
        "id,result,duration,executionDate\n"
        "EXEC-001,PASS,5.2,2026-01-01\n"
        "EXEC-001,FAIL,12.0,2026-01-02\n",
    )

    issues = validate_dataset_rows(
        make_contract(),
        tmp_path,
    )

    assert any(
        "duplicate primary key" in issue
        for issue in issues
    )