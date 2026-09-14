import asyncio

from agent_service import AgentService
from llm_client import LLMClient
from neo4j_client import Neo4jClient
from query_service import QueryService


async def main():
    llm = LLMClient()
    neo4j = Neo4jClient()

    await llm.start()

    try:
        neo4j.verify_connection()

        query_service = QueryService(
            llm_client=llm,
            neo4j_client=neo4j,
        )

        agent = AgentService(
            llm_client=llm,
            query_service=query_service,
        )

        print(
            "Minimal Knowledge Graph Tool-Calling Agent"
        )
        print(
            f"Configured model: {llm.model}"
        )
        print(
            "Available custom tool: graph_retrieval"
        )
        print(
            "Type 'exit' to stop."
        )

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
                response = (
                    await agent.answer_question(
                        question
                    )
                )

                print("\nTOOL DECISION")

                if response.graph_tool_used:
                    print(
                        "graph_retrieval: USED"
                    )
                    print(
                        "Tool calls: "
                        f"{response.graph_tool_calls}"
                    )
                    print(
                        "Successful calls: "
                        f"{response.graph_tool_successes}"
                    )
                    print(
                        "Retrieved records: "
                        f"{response.retrieved_record_count}"
                    )

                    if (
                        response.cypher_generation_attempts
                        is not None
                    ):
                        print(
                            "Cypher generation attempts: "
                            f"{response.cypher_generation_attempts}"
                        )

                    if response.retry_reason:
                        print(
                            "Retrieval retry reason: "
                            f"{response.retry_reason}"
                        )

                    if response.tool_error:
                        print(
                            "Tool error: "
                            f"{response.tool_error}"
                        )

                else:
                    print(
                        "graph_retrieval: NOT USED"
                    )

                print("\nAGENT ANSWER")
                print(response.answer)

            except Exception as error:
                print("\nERROR")
                print(error)

    finally:
        neo4j.close()
        await llm.stop()


if __name__ == "__main__":
    asyncio.run(main())