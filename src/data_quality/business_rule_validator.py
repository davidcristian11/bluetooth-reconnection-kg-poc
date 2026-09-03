from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

from data_quality.reference_validator import load_rows


def _find_business_rule(
    contract: dict[str, Any],
    rule_name: str,
) -> dict[str, Any] | None:
    rules = contract.get("businessRules", [])

    for rule in rules:
        if rule.get("name") == rule_name:
            return rule

    return None


def validate_trace_execution_dates(
    contracts: dict[str, dict[str, Any]],
    project_root: str | Path,
) -> list[str]:
    required_datasets = {
        "test_executions",
        "test_traces",
        "test_execution_produces_trace",
    }

    missing_datasets = sorted(
        required_datasets - set(contracts)
    )

    if missing_datasets:
        return [
            "Cannot validate trace dates; "
            f"missing datasets: {missing_datasets}"
        ]

    execution_date_format = contracts[
        "test_executions"
    ]["columns"]["executionDate"].get("format")

    trace_timestamp_format = contracts[
        "test_traces"
    ]["columns"]["timestamp"].get("format")

    if not isinstance(execution_date_format, str):
        return [
            "test_executions.executionDate has no format"
        ]

    if not isinstance(trace_timestamp_format, str):
        return [
            "test_traces.timestamp has no format"
        ]

    root = Path(project_root)

    executions = load_rows(
        contracts["test_executions"],
        root,
    )
    traces = load_rows(
        contracts["test_traces"],
        root,
    )
    relationships = load_rows(
        contracts["test_execution_produces_trace"],
        root,
    )

    execution_dates = {
        execution["id"]: datetime.strptime(
            execution["executionDate"],
            execution_date_format,
        ).date()
        for execution in executions
    }

    execution_by_trace = {
        relationship["traceId"]:
            relationship["executionId"]
        for relationship in relationships
    }

    issues: list[str] = []

    for trace in traces:
        trace_id = trace["id"]
        execution_id = execution_by_trace.get(trace_id)

        if execution_id is None:
            continue

        trace_date = datetime.strptime(
            trace["timestamp"],
            trace_timestamp_format,
        ).date()

        execution_date = execution_dates[execution_id]

        if trace_date != execution_date:
            issues.append(
                "trace_matches_execution_date: "
                f"trace '{trace_id}' has date "
                f"'{trace_date}', but execution "
                f"'{execution_id}' has date "
                f"'{execution_date}'"
            )

    return issues


def validate_defect_execution_consistency(
    contracts: dict[str, dict[str, Any]],
    project_root: str | Path,
) -> list[str]:
    required_datasets = {
        "defect_tickets",
        "test_executions",
        "test_execution_has_defect_ticket",
    }

    missing_datasets = sorted(
        required_datasets - set(contracts)
    )

    if missing_datasets:
        return [
            "Cannot validate defect consistency; "
            f"missing datasets: {missing_datasets}"
        ]

    root = Path(project_root)

    defects = load_rows(
        contracts["defect_tickets"],
        root,
    )
    executions = load_rows(
        contracts["test_executions"],
        root,
    )
    relationships = load_rows(
        contracts[
            "test_execution_has_defect_ticket"
        ],
        root,
    )

    result_by_execution = {
        execution["id"]: execution["result"]
        for execution in executions
    }

    defects_linked_to_failed_executions: set[str] = set()
    issues: list[str] = []

    for relationship in relationships:
        execution_id = relationship["executionId"]
        defect_id = relationship["defectTicketId"]
        result = result_by_execution[execution_id]

        if result == "FAIL":
            defects_linked_to_failed_executions.add(
                defect_id
            )

        if result == "PASS":
            issues.append(
                "passed_execution_has_no_defect: "
                f"execution '{execution_id}' has result "
                f"'PASS', but is linked to defect "
                f"'{defect_id}'"
            )

    for defect in defects:
        defect_id = defect["id"]

        if (
            defect_id
            not in defects_linked_to_failed_executions
        ):
            issues.append(
                "defect_is_linked_to_failed_execution: "
                f"defect '{defect_id}' is not linked "
                f"to any failed execution"
            )

    return issues


def validate_reconnection_threshold(
    contracts: dict[str, dict[str, Any]],
    project_root: str | Path,
) -> list[str]:
    required_datasets = {
        "requirements",
        "test_executions",
        "test_execution_execution_of_test",
        "test_verifies_requirement",
    }

    missing_datasets = sorted(
        required_datasets - set(contracts)
    )

    if missing_datasets:
        return [
            "Cannot validate reconnection threshold; "
            f"missing datasets: {missing_datasets}"
        ]

    rule = _find_business_rule(
        contracts["requirements"],
        "reconnection_time_threshold",
    )

    if rule is None:
        return [
            "Missing business rule: "
            "reconnection_time_threshold"
        ]

    requirement_id = rule.get(
        "appliesToRequirementId"
    )
    maximum_seconds = rule.get("maximumSeconds")

    if not isinstance(requirement_id, str):
        return [
            "reconnection_time_threshold must define "
            "appliesToRequirementId"
        ]

    if not isinstance(maximum_seconds, (int, float)):
        return [
            "reconnection_time_threshold must define "
            "a numeric maximumSeconds"
        ]

    root = Path(project_root)

    executions = load_rows(
        contracts["test_executions"],
        root,
    )
    execution_relationships = load_rows(
        contracts[
            "test_execution_execution_of_test"
        ],
        root,
    )
    verification_relationships = load_rows(
        contracts["test_verifies_requirement"],
        root,
    )

    execution_to_tests: dict[str, set[str]] = defaultdict(
        set
    )

    for relationship in execution_relationships:
        execution_to_tests[
            relationship["executionId"]
        ].add(relationship["testId"])

    test_to_requirements: dict[str, set[str]] = (
        defaultdict(set)
    )

    for relationship in verification_relationships:
        test_to_requirements[
            relationship["testId"]
        ].add(relationship["requirementId"])

    issues: list[str] = []

    for row_number, execution in enumerate(
        executions,
        start=2,
    ):
        execution_id = execution["id"]
        measurement = execution.get(
            "reconnectionTimeSeconds",
            "",
        )

        if not measurement:
            continue

        test_ids = execution_to_tests.get(
            execution_id,
            set(),
        )

        verifies_requirement = any(
            requirement_id
            in test_to_requirements.get(test_id, set())
            for test_id in test_ids
        )

        if not verifies_requirement:
            continue

        measured_seconds = float(measurement)

        if (
            measured_seconds > maximum_seconds
            and execution["result"] != "FAIL"
        ):
            issues.append(
                f"test_executions row {row_number}: "
                f"execution '{execution_id}' took "
                f"{measured_seconds} seconds, exceeding "
                f"the {maximum_seconds}-second limit for "
                f"'{requirement_id}', but result is "
                f"'{execution['result']}' instead of 'FAIL'"
            )

    return issues


def validate_business_rules(
    contracts: dict[str, dict[str, Any]],
    project_root: str | Path,
) -> list[str]:
    issues: list[str] = []

    issues.extend(
        validate_reconnection_threshold(
            contracts,
            project_root,
        )
    )

    issues.extend(
        validate_trace_execution_dates(
            contracts,
            project_root,
        )
    )

    issues.extend(
        validate_defect_execution_consistency(
            contracts,
            project_root,
        )
    )

    return issues