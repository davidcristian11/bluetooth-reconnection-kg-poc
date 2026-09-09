from argparse import Namespace

import rebuild_neo4j as rebuild


class FakeRebuildClient:
    def __init__(self):
        self.uri = "neo4j://localhost:7687"
        self.database = "neo4j"
        self.script_names = []
        self.closed = False

    def verify_connection(self):
        pass

    def assert_safe_to_reset(self, confirmation):
        pass

    def run_cypher_script(self, path):
        self.script_names.append(path.name)
        return 1

    def close(self):
        self.closed = True


def test_rebuild_cycle_executes_scripts_in_required_order(
    monkeypatch,
):
    client = FakeRebuildClient()

    monkeypatch.setattr(
        rebuild,
        "validate_post_import",
        lambda client: "fingerprint-1",
    )

    fingerprint = rebuild.run_rebuild_cycle(client)

    assert client.script_names == [
        "00-reset-graph.cypher",
        "01-create-constraints.cypher",
        "02-import-nodes.cypher",
        "03-import-relationships.cypher",
    ]
    assert fingerprint == "fingerprint-1"


def test_main_stops_before_neo4j_when_source_data_is_invalid(
    monkeypatch,
):
    monkeypatch.setattr(
        rebuild,
        "parse_args",
        lambda: Namespace(
            confirm_reset="unused",
            verify_repeatability=False,
        ),
    )
    monkeypatch.setattr(
        rebuild,
        "validate_source_data",
        lambda: 1,
    )

    def fail_if_client_is_created():
        raise AssertionError(
            "Neo4j client must not be created after "
            "source-data validation failure."
        )

    monkeypatch.setattr(
        rebuild,
        "Neo4jRebuildClient",
        fail_if_client_is_created,
    )

    assert rebuild.main() == 1


def test_main_fails_when_repeatability_fingerprint_changes(
    monkeypatch,
):
    client = FakeRebuildClient()
    fingerprints = iter(
        ["fingerprint-1", "fingerprint-2"]
    )

    monkeypatch.setattr(
        rebuild,
        "parse_args",
        lambda: Namespace(
            confirm_reset=(
                "RESET bluetooth-reconnection-kg-poc/neo4j"
            ),
            verify_repeatability=True,
        ),
    )
    monkeypatch.setattr(
        rebuild,
        "validate_source_data",
        lambda: 0,
    )
    monkeypatch.setattr(
        rebuild,
        "Neo4jRebuildClient",
        lambda: client,
    )
    monkeypatch.setattr(
        rebuild,
        "run_rebuild_cycle",
        lambda client, prefix="": next(fingerprints),
    )

    assert rebuild.main() == 1
    assert client.closed is True