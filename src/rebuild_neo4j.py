import argparse
from pathlib import Path
import sys

from neo4j_post_import_validation import validate_post_import
from neo4j_rebuild import (
    Neo4jRebuildClient,
    expected_reset_confirmation,
)
from validate_data import main as validate_source_data


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CYPHER_DIRECTORY = PROJECT_ROOT / "cypher"

RESET_SCRIPT = CYPHER_DIRECTORY / "00-reset-graph.cypher"
CONSTRAINTS_SCRIPT = (
    CYPHER_DIRECTORY / "01-create-constraints.cypher"
)
NODE_IMPORT_SCRIPT = (
    CYPHER_DIRECTORY / "02-import-nodes.cypher"
)
RELATIONSHIP_IMPORT_SCRIPT = (
    CYPHER_DIRECTORY / "03-import-relationships.cypher"
)


class RebuildError(RuntimeError):
    pass


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Rebuild the local Bluetooth reconnection "
            "Neo4j graph from validated source CSV data."
        )
    )

    parser.add_argument(
        "--confirm-reset",
        required=True,
        help=(
            "Explicit destructive reset confirmation. "
            "For the default database use: "
            "RESET bluetooth-reconnection-kg-poc/neo4j"
        ),
    )

    parser.add_argument(
        "--verify-repeatability",
        action="store_true",
        help=(
            "Run a second rebuild and verify that both "
            "graph fingerprints are identical."
        ),
    )

    return parser.parse_args()


def run_script_step(
    client: Neo4jRebuildClient,
    title: str,
    path: Path,
) -> None:
    print(f"\n{title}")

    statement_count = client.run_cypher_script(path)

    print(
        f"Executed {statement_count} Cypher "
        f"statement(s) from {path.name}."
    )


def run_rebuild_cycle(
    client: Neo4jRebuildClient,
    prefix: str = "",
) -> str:
    run_script_step(
        client,
        f"{prefix}Clean existing graph",
        RESET_SCRIPT,
    )

    run_script_step(
        client,
        f"{prefix}Apply constraints",
        CONSTRAINTS_SCRIPT,
    )

    run_script_step(
        client,
        f"{prefix}Import nodes",
        NODE_IMPORT_SCRIPT,
    )

    run_script_step(
        client,
        f"{prefix}Import relationships",
        RELATIONSHIP_IMPORT_SCRIPT,
    )

    print(f"\n{prefix}Run post-import validation")

    return validate_post_import(client)


def main() -> int:
    args = parse_args()
    client = None

    try:
        print("[1] Validate source data")

        validation_exit_code = validate_source_data()

        if validation_exit_code != 0:
            raise RebuildError(
                "Source data validation failed. "
                "Neo4j was not modified."
            )

        print("\n[2] Connect to Neo4j")

        client = Neo4jRebuildClient()
        client.verify_connection()

        print(
            "Connected to "
            f"{client.uri}, database={client.database}."
        )

        print("\n[3] Verify reset safety guard")

        client.assert_safe_to_reset(
            args.confirm_reset
        )

        print(
            "Safety guard passed for confirmation: "
            f"{expected_reset_confirmation(client.database)}"
        )

        print("\n[4-8] Rebuild graph")

        first_fingerprint = run_rebuild_cycle(
            client,
            prefix="First rebuild: ",
        )

        if args.verify_repeatability:
            print("\n[9] Verify repeatability")

            second_fingerprint = run_rebuild_cycle(
                client,
                prefix="Second rebuild: ",
            )

            if second_fingerprint != first_fingerprint:
                raise RebuildError(
                    "Repeatability check failed: graph "
                    "fingerprints are different."
                )

            print(
                "Repeatability check passed: both rebuilds "
                "produced the same graph fingerprint."
            )

        print(
            "\nNEO4J REBUILD COMPLETED SUCCESSFULLY."
        )

        return 0

    except Exception as exc:
        print(
            f"\nREBUILD FAILED: {exc}",
            file=sys.stderr,
        )
        return 1

    finally:
        if client is not None:
            client.close()


if __name__ == "__main__":
    raise SystemExit(main())