from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from data_quality.reference_validator import load_rows


@dataclass(frozen=True)
class CoverageRule:
    name: str
    source_dataset: str
    source_column: str
    relationship_dataset: str
    relationship_column: str
    minimum_matches: int = 1
    maximum_matches: int | None = None
    condition_column: str | None = None
    condition_value: str | None = None


COVERAGE_RULES = [
    CoverageRule(
        name="feature_has_requirement",
        source_dataset="features",
        source_column="id",
        relationship_dataset="feature_has_requirement",
        relationship_column="featureId",
    ),
    CoverageRule(
        name="requirement_belongs_to_feature",
        source_dataset="requirements",
        source_column="id",
        relationship_dataset="feature_has_requirement",
        relationship_column="requirementId",
    ),
    CoverageRule(
        name="approved_requirement_is_implemented",
        source_dataset="requirements",
        source_column="id",
        relationship_dataset=(
            "software_component_implements_requirement"
        ),
        relationship_column="requirementId",
        condition_column="status",
        condition_value="Approved",
    ),
    CoverageRule(
        name="approved_requirement_has_test_coverage",
        source_dataset="requirements",
        source_column="id",
        relationship_dataset="test_verifies_requirement",
        relationship_column="requirementId",
        condition_column="status",
        condition_value="Approved",
    ),
    CoverageRule(
        name="component_implements_requirement",
        source_dataset="software_components",
        source_column="id",
        relationship_dataset=(
            "software_component_implements_requirement"
        ),
        relationship_column="componentId",
    ),
    CoverageRule(
        name="test_verifies_requirement",
        source_dataset="tests",
        source_column="id",
        relationship_dataset="test_verifies_requirement",
        relationship_column="testId",
    ),
    CoverageRule(
        name="execution_has_exactly_one_test",
        source_dataset="test_executions",
        source_column="id",
        relationship_dataset=(
            "test_execution_execution_of_test"
        ),
        relationship_column="executionId",
        minimum_matches=1,
        maximum_matches=1,
    ),
    CoverageRule(
        name="trace_has_exactly_one_execution",
        source_dataset="test_traces",
        source_column="id",
        relationship_dataset=(
            "test_execution_produces_trace"
        ),
        relationship_column="traceId",
        minimum_matches=1,
        maximum_matches=1,
    ),
    CoverageRule(
        name="defect_affects_component",
        source_dataset="defect_tickets",
        source_column="id",
        relationship_dataset=(
            "defect_ticket_affects_component"
        ),
        relationship_column="defectTicketId",
    ),
]


def validate_coverage_rule(
    rule: CoverageRule,
    rows_by_dataset: dict[
        str,
        list[dict[str, str]],
    ],
) -> list[str]:
    source_rows = rows_by_dataset[rule.source_dataset]
    relationship_rows = rows_by_dataset[
        rule.relationship_dataset
    ]

    relationship_counts = Counter(
        row[rule.relationship_column]
        for row in relationship_rows
    )

    issues: list[str] = []

    for row in source_rows:
        if (
            rule.condition_column is not None
            and row.get(rule.condition_column)
            != rule.condition_value
        ):
            continue

        source_id = row[rule.source_column]
        match_count = relationship_counts[source_id]

        if match_count < rule.minimum_matches:
            issues.append(
                f"{rule.name}: "
                f"{rule.source_dataset}.{rule.source_column} "
                f"'{source_id}' has {match_count} matching "
                f"relationships; minimum is "
                f"{rule.minimum_matches}"
            )

        if (
            rule.maximum_matches is not None
            and match_count > rule.maximum_matches
        ):
            issues.append(
                f"{rule.name}: "
                f"{rule.source_dataset}.{rule.source_column} "
                f"'{source_id}' has {match_count} matching "
                f"relationships; maximum is "
                f"{rule.maximum_matches}"
            )

    return issues


def validate_relationship_coverage(
    contracts: dict,
    project_root: str | Path,
) -> list[str]:
    required_datasets = {
        rule.source_dataset
        for rule in COVERAGE_RULES
    } | {
        rule.relationship_dataset
        for rule in COVERAGE_RULES
    }

    missing_datasets = sorted(
        required_datasets - set(contracts)
    )

    if missing_datasets:
        return [
            "Cannot validate relationship coverage; "
            f"missing datasets: {missing_datasets}"
        ]

    root = Path(project_root)

    rows_by_dataset = {
        dataset_name: load_rows(
            contracts[dataset_name],
            root,
        )
        for dataset_name in required_datasets
    }

    issues: list[str] = []

    for rule in COVERAGE_RULES:
        issues.extend(
            validate_coverage_rule(
                rule,
                rows_by_dataset,
            )
        )

    return issues