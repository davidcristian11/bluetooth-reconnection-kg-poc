from pathlib import Path
from urllib.parse import urlparse
import os

from dotenv import load_dotenv
from neo4j import GraphDatabase, Query, RoutingControl


load_dotenv()

PROJECT_NAME = "bluetooth-reconnection-kg-poc"
LOCAL_NEO4J_HOSTS = {
    "localhost",
    "127.0.0.1",
    "::1",
}
DEFAULT_REBUILD_TIMEOUT_SECONDS = 30.0


class RebuildSafetyError(RuntimeError):
    pass


class CypherScriptError(RuntimeError):
    pass


def expected_reset_confirmation(database: str) -> str:
    return f"RESET {PROJECT_NAME}/{database}"


def validate_reset_safety(
    uri: str,
    database: str,
    confirmation: str,
) -> None:
    hostname = urlparse(uri).hostname

    if hostname not in LOCAL_NEO4J_HOSTS:
        raise RebuildSafetyError(
            "Rebuild is allowed only for a local Neo4j instance. "
            f"Configured host: {hostname!r}."
        )

    expected_confirmation = expected_reset_confirmation(
        database
    )

    if confirmation != expected_confirmation:
        raise RebuildSafetyError(
            "Reset confirmation does not match the target database. "
            f"Expected exactly: {expected_confirmation!r}."
        )


def load_cypher_statements(path: Path) -> list[str]:
    if not path.is_file():
        raise CypherScriptError(
            f"Cypher script does not exist: {path}"
        )

    script = path.read_text(encoding="utf-8")
    statements = [
        statement.strip()
        for statement in script.split(";")
        if statement.strip()
    ]

    if not statements:
        raise CypherScriptError(
            f"Cypher script is empty: {path}"
        )

    return statements


class Neo4jRebuildClient:
    def __init__(self):
        self.uri = os.getenv(
            "NEO4J_URI",
            "neo4j://localhost:7687",
        )
        self.user = os.getenv(
            "NEO4J_USER",
            "neo4j",
        )
        self.password = os.getenv("NEO4J_PASSWORD")
        self.database = os.getenv(
            "NEO4J_DATABASE",
            "neo4j",
        )

        if not self.password:
            raise ValueError(
                "NEO4J_PASSWORD is missing from .env"
            )

        self.driver = GraphDatabase.driver(
            self.uri,
            auth=(self.user, self.password),
        )

    def verify_connection(self) -> None:
        self.driver.verify_connectivity()

    def assert_safe_to_reset(
        self,
        confirmation: str,
    ) -> None:
        validate_reset_safety(
            uri=self.uri,
            database=self.database,
            confirmation=confirmation,
        )

    def run_cypher_script(
        self,
        path: Path,
    ) -> int:
        statements = load_cypher_statements(path)

        for statement in statements:
            query = Query(
                statement,
                timeout=DEFAULT_REBUILD_TIMEOUT_SECONDS,
            )

            self.driver.execute_query(
                query,
                database_=self.database,
                routing_=RoutingControl.WRITE,
            )

        return len(statements)

    def run_query(
        self,
        cypher: str,
        **parameters,
    ) -> list[dict]:
        query = Query(
            cypher,
            timeout=DEFAULT_REBUILD_TIMEOUT_SECONDS,
        )

        records, _, _ = self.driver.execute_query(
            query,
            parameters_=parameters,
            database_=self.database,
            routing_=RoutingControl.READ,
        )

        return [record.data() for record in records]

    def close(self) -> None:
        self.driver.close()