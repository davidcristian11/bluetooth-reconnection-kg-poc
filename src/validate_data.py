from pathlib import Path

from data_quality.contract_loader import (
    ContractLoadError,
    load_contracts,
)
from data_quality.coverage_validator import validate_relationship_coverage
from data_quality.dataset_validator import (
    validate_all_dataset_structures,
)
from data_quality.row_validator import (
    validate_all_dataset_rows,
)
from data_quality.reference_validator import (
    validate_references,
)
from data_quality.business_rule_validator import (
    validate_business_rules,
)

def main() -> int:
    project_root = Path(__file__).resolve().parents[1]
    contracts_directory = project_root / "contracts"

    try:
        contracts = load_contracts(contracts_directory)
    except ContractLoadError as exc:
        print(f"CONTRACT ERROR: {exc}")
        return 1

    issues = validate_all_dataset_structures(
        contracts,
        project_root,
    )

    if not issues:
        issues = validate_references(
            contracts,
            project_root,
        )

    if not issues:
        issues = validate_relationship_coverage(
            contracts,
            project_root,
        )

    if not issues:
        issues = validate_business_rules(
            contracts,
            project_root,
        )

    if not issues:
        issues = validate_all_dataset_rows(
            contracts,
            project_root,
        )

    if issues:
        print("DATA VALIDATION FAILED")

        for issue in issues:
            print(f"- {issue}")

        return 1

    print(
        f"DATA VALIDATION PASSED: "
        f"{len(contracts)} datasets validated."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())