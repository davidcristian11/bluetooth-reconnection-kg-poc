from pathlib import Path

from data_quality.contract_loader import load_contracts
from validate_data import main


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_all_project_contracts_are_present():
    contracts = load_contracts(
        PROJECT_ROOT / "contracts"
    )

    assert len(contracts) == 14


def test_repository_data_passes_full_validation():
    exit_code = main()

    assert exit_code == 0