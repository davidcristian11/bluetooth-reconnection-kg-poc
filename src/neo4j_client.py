import os

from dotenv import load_dotenv
from neo4j import GraphDatabase, RoutingControl


load_dotenv()


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

        if not password:
            raise ValueError(
                "NEO4J_PASSWORD is missing from .env"
            )

        self.driver = GraphDatabase.driver(
            uri,
            auth=(user, password),
        )

    def verify_connection(self) -> None:
        self.driver.verify_connectivity()

    def run_query(self, cypher: str):
        records, _, _ = self.driver.execute_query(
            cypher,
            database_=self.database,
            routing_=RoutingControl.READ,
        )

        return [
            record.data()
            for record in records
        ]

    def close(self) -> None:
        self.driver.close()