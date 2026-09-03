import os

from dotenv import load_dotenv
from neo4j import GraphDatabase, Query, RoutingControl


load_dotenv()


class QueryResultLimitError(RuntimeError):
    pass


def _collect_limited_records(result, max_records: int):
    records = result.fetch(max_records + 1)
    result.consume()

    if len(records) > max_records:
        raise QueryResultLimitError(
            "Neo4j query returned more than "
            f"{max_records} records."
        )

    return [
        record.data()
        for record in records
    ]


class Neo4jClient:
    def __init__(self):
        uri = os.getenv(
            "NEO4J_URI",
            "neo4j://localhost:7687",
        )

        user = os.getenv(
            "NEO4J_USER",
            "neo4j",
        )

        password = os.getenv("NEO4J_PASSWORD")

        self.database = os.getenv(
            "NEO4J_DATABASE",
            "neo4j",
        )

        self.query_timeout_seconds = float(
            os.getenv(
                "NEO4J_QUERY_TIMEOUT_SECONDS",
                "5",
            )
        )

        self.max_records = int(
            os.getenv(
                "NEO4J_MAX_RECORDS",
                "100",
            )
        )

        if not password:
            raise ValueError(
                "NEO4J_PASSWORD is missing from .env"
            )

        if self.query_timeout_seconds <= 0:
            raise ValueError(
                "NEO4J_QUERY_TIMEOUT_SECONDS "
                "must be greater than zero."
            )

        if self.max_records <= 0:
            raise ValueError(
                "NEO4J_MAX_RECORDS "
                "must be greater than zero."
            )

        self.driver = GraphDatabase.driver(
            uri,
            auth=(user, password),
        )

    def verify_connection(self) -> None:
        self.driver.verify_connectivity()

    def run_query(self, cypher: str):
        query = Query(
            cypher,
            timeout=self.query_timeout_seconds,
        )

        return self.driver.execute_query(
            query,
            database_=self.database,
            routing_=RoutingControl.READ,
            result_transformer_=lambda result: (
                _collect_limited_records(
                    result,
                    self.max_records,
                )
            ),
        )

    def close(self) -> None:
        self.driver.close()