import asyncio
import json

from llm_client import LLMClient
from neo4j_client import Neo4jClient
from query_service import QueryService


async def main():
    llm = LLMClient()
    neo4j = Neo4jClient()

    await llm.start()

    try:
        neo4j.verify_connection()

        service = QueryService(
            llm_client=llm,
            neo4j_client=neo4j,
        )

        print(
            "Ontology-aware Knowledge Graph querying"
        )
        print("Type 'exit' to stop.")

        while True:
            question = input(
                "\nAsk a question: "
            ).strip()

            if question.lower() in {
                "exit",
                "quit",
            }:
                break

            if not question:
                continue

            try:
                response = await service.answer_question(
                    question
                )

                print("\nGENERATED CYPHER")
                print(response.cypher)

                print("\nNEO4J RESULT")
                print(
                    json.dumps(
                        response.records,
                        indent=2,
                        default=str,
                    )
                )

                if response.generation_attempts > 1:
                    print(
                        "\nNOTE"
                    )
                    print(
                        "The first Cypher attempt failed "
                        "and was automatically corrected."
                    )

                print("\nAI ANSWER")
                print(response.answer)

            except Exception as error:
                print("\nERROR")
                print(error)

    finally:
        neo4j.close()
        await llm.stop()


if __name__ == "__main__":
    asyncio.run(main())