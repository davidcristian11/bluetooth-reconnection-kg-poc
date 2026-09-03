from data_quality.business_rule_validator import (
    validate_defect_execution_consistency,
    validate_reconnection_threshold,
    validate_trace_execution_dates,
)


def make_contracts() -> dict:
    return {
        "requirements": {
            "dataset": {
                "name": "requirements",
                "path": "data/requirements.csv",
            },
            "businessRules": [
                {
                    "name": "reconnection_time_threshold",
                    "appliesToRequirementId": "REQ-002",
                    "maximumSeconds": 10.0,
                }
            ],
        },
        "test_executions": {
            "dataset": {
                "name": "test_executions",
                "path": "data/test_executions.csv",
            },
        },
        "test_execution_execution_of_test": {
            "dataset": {
                "name":
                    "test_execution_execution_of_test",
                "path": "data/execution_of.csv",
            },
        },
        "test_verifies_requirement": {
            "dataset": {
                "name": "test_verifies_requirement",
                "path": "data/verifies.csv",
            },
        },
    }


def write_datasets(tmp_path, result: str):
    data_directory = tmp_path / "data"
    data_directory.mkdir()

    (data_directory / "test_executions.csv").write_text(
        "id,result,reconnectionTimeSeconds\n"
        f"EXEC-001,{result},12.0\n",
        encoding="utf-8",
    )

    (data_directory / "execution_of.csv").write_text(
        "executionId,testId\n"
        "EXEC-001,TEST-001\n",
        encoding="utf-8",
    )

    (data_directory / "verifies.csv").write_text(
        "testId,requirementId\n"
        "TEST-001,REQ-002\n",
        encoding="utf-8",
    )


def test_accepts_threshold_violation_marked_fail(
    tmp_path,
):
    write_datasets(tmp_path, "FAIL")

    issues = validate_reconnection_threshold(
        make_contracts(),
        tmp_path,
    )

    assert issues == []


def test_rejects_threshold_violation_marked_pass(
    tmp_path,
):
    write_datasets(tmp_path, "PASS")

    issues = validate_reconnection_threshold(
        make_contracts(),
        tmp_path,
    )

    assert any(
        "instead of 'FAIL'" in issue
        for issue in issues
    )


def make_trace_contracts() -> dict:
    return {
        "test_executions": {
            "dataset": {
                "name": "test_executions",
                "path": "data/executions.csv",
            },
            "columns": {
                "executionDate": {
                    "format": "%Y-%m-%d",
                },
            },
        },
        "test_traces": {
            "dataset": {
                "name": "test_traces",
                "path": "data/traces.csv",
            },
            "columns": {
                "timestamp": {
                    "format": "%Y-%m-%dT%H:%M:%S",
                },
            },
        },
        "test_execution_produces_trace": {
            "dataset": {
                "name":
                    "test_execution_produces_trace",
                "path": "data/produces.csv",
            },
        },
    }


def write_trace_datasets(tmp_path, trace_date: str):
    data_directory = tmp_path / "data"
    data_directory.mkdir()

    (data_directory / "executions.csv").write_text(
        "id,executionDate\n"
        "EXEC-001,2026-07-21\n",
        encoding="utf-8",
    )

    (data_directory / "traces.csv").write_text(
        "id,timestamp\n"
        f"TRACE-001,{trace_date}T08:45:03\n",
        encoding="utf-8",
    )

    (data_directory / "produces.csv").write_text(
        "executionId,traceId\n"
        "EXEC-001,TRACE-001\n",
        encoding="utf-8",
    )


def test_accepts_trace_on_execution_date(tmp_path):
    write_trace_datasets(tmp_path, "2026-07-21")

    issues = validate_trace_execution_dates(
        make_trace_contracts(),
        tmp_path,
    )

    assert issues == []


def test_rejects_trace_on_different_date(tmp_path):
    write_trace_datasets(tmp_path, "2026-07-22")

    issues = validate_trace_execution_dates(
        make_trace_contracts(),
        tmp_path,
    )

    assert any(
        "trace_matches_execution_date" in issue
        for issue in issues
    )


def make_defect_contracts() -> dict:
    return {
        "defect_tickets": {
            "dataset": {
                "name": "defect_tickets",
                "path": "data/defects.csv",
            },
        },
        "test_executions": {
            "dataset": {
                "name": "test_executions",
                "path": "data/executions.csv",
            },
        },
        "test_execution_has_defect_ticket": {
            "dataset": {
                "name":
                    "test_execution_has_defect_ticket",
                "path": "data/has_defect.csv",
            },
        },
    }


def write_defect_datasets(tmp_path, result: str):
    data_directory = tmp_path / "data"
    data_directory.mkdir()

    (data_directory / "defects.csv").write_text(
        "id\nDEF-001\n",
        encoding="utf-8",
    )

    (data_directory / "executions.csv").write_text(
        "id,result\n"
        f"EXEC-001,{result}\n",
        encoding="utf-8",
    )

    (data_directory / "has_defect.csv").write_text(
        "executionId,defectTicketId\n"
        "EXEC-001,DEF-001\n",
        encoding="utf-8",
    )


def test_accepts_defect_linked_to_failed_execution(
    tmp_path,
):
    write_defect_datasets(tmp_path, "FAIL")

    issues = validate_defect_execution_consistency(
        make_defect_contracts(),
        tmp_path,
    )

    assert issues == []


def test_rejects_defect_linked_to_passed_execution(
    tmp_path,
):
    write_defect_datasets(tmp_path, "PASS")

    issues = validate_defect_execution_consistency(
        make_defect_contracts(),
        tmp_path,
    )

    assert any(
        "passed_execution_has_no_defect" in issue
        for issue in issues
    )

    assert any(
        "defect_is_linked_to_failed_execution" in issue
        for issue in issues
    )