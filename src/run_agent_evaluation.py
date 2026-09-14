import argparse
import asyncio
import json
from dataclasses import asdict
from pathlib import Path

from agent_benchmark import (
    AgentBenchmarkCase,
    load_agent_benchmark,
)
from agent_evaluation import (
    AgentEvaluation,
    evaluate_agent_response,
)
from agent_service import (
    AgentResponse,
    AgentService,
)
from llm_client import LLMClient
from neo4j_client import Neo4jClient
from query_service import QueryService


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Evaluate the minimal tool-calling agent."
        )
    )

    parser.add_argument(
        "--benchmark",
        default=(
            "evaluation/agent_benchmark.yaml"
        ),
        help=(
            "Path to the agent benchmark YAML."
        ),
    )

    parser.add_argument(
        "--case",
        help=(
            "Run only one benchmark case, "
            "for example AGT-001."
        ),
    )

    parser.add_argument(
        "--output",
        help=(
            "Optional path for structured "
            "JSON results."
        ),
    )

    return parser.parse_args()


def select_agent_cases(
    cases: tuple[AgentBenchmarkCase, ...],
    case_id: str | None,
) -> tuple[AgentBenchmarkCase, ...]:
    if case_id is None:
        return cases

    selected = tuple(
        case
        for case in cases
        if case.id == case_id
    )

    if not selected:
        raise ValueError(
            f"Unknown agent benchmark case: "
            f"{case_id}"
        )

    return selected


def build_summary(
    results: list[dict],
) -> dict:
    total = len(results)

    if total == 0:
        return {
            "cases": 0,
            "executed": 0,
            "fullyCorrect": 0,
            "toolSelectionCorrect": 0,
            "toolCallCountCorrect": 0,
            "toolExecutionSuccess": 0,
            "answerValuesComplete": 0,
            "noResultHandlingCorrect": 0,
        }

    executed = sum(
        result["error"] is None
        for result in results
    )

    successful_results = [
        result
        for result in results
        if result["evaluation"] is not None
    ]

    def count_metric(
        metric_name: str,
    ) -> int:
        return sum(
            result["evaluation"][
                metric_name
            ]
            for result in successful_results
        )

    return {
        "cases": total,
        "executed": executed,
        "fullyCorrect": count_metric(
            "fully_correct"
        ),
        "toolSelectionCorrect": count_metric(
            "tool_selection_correct"
        ),
        "toolCallCountCorrect": count_metric(
            "tool_call_count_correct"
        ),
        "toolExecutionSuccess": count_metric(
            "tool_execution_success"
        ),
        "answerValuesComplete": count_metric(
            "answer_values_complete"
        ),
        "noResultHandlingCorrect": count_metric(
            "no_result_handling_correct"
        ),
    }


def _response_to_dict(
    response: AgentResponse,
) -> dict:
    return asdict(response)


def _evaluation_to_dict(
    evaluation: AgentEvaluation,
) -> dict:
    return asdict(evaluation)


async def run_case(
    agent: AgentService,
    case: AgentBenchmarkCase,
) -> dict:
    try:
        response = await agent.answer_question(
            case.question
        )

        evaluation = evaluate_agent_response(
            case,
            response,
        )

        return {
            "caseId": case.id,
            "category": case.category,
            "question": case.question,
            "expected": {
                "graphToolRequired": (
                    case.expected.graph_tool_required
                ),
                "maxGraphToolCalls": (
                    case.expected.max_graph_tool_calls
                ),
                "requiredAnswerValues": list(
                    case.expected.required_answer_values
                ),
                "expectNoResultAnswer": (
                    case.expected.expect_no_result_answer
                ),
            },
            "response": _response_to_dict(
                response
            ),
            "evaluation": (
                _evaluation_to_dict(
                    evaluation
                )
            ),
            "error": None,
        }

    except Exception as error:
        return {
            "caseId": case.id,
            "category": case.category,
            "question": case.question,
            "expected": {
                "graphToolRequired": (
                    case.expected.graph_tool_required
                ),
                "maxGraphToolCalls": (
                    case.expected.max_graph_tool_calls
                ),
                "requiredAnswerValues": list(
                    case.expected.required_answer_values
                ),
                "expectNoResultAnswer": (
                    case.expected.expect_no_result_answer
                ),
            },
            "response": None,
            "evaluation": None,
            "error": str(error),
        }


def print_case_result(
    result: dict,
) -> None:
    print()
    print(
        f"[{result['caseId']}] "
        f"{result['category']}"
    )
    print(
        f"Question: {result['question']}"
    )

    if result["error"] is not None:
        print(
            f"ERROR: {result['error']}"
        )
        return

    response = result["response"]
    evaluation = result["evaluation"]

    print(
        "Graph tool: "
        + (
            "USED"
            if response["graph_tool_used"]
            else "NOT USED"
        )
    )

    print(
        "Tool calls: "
        f"{response['graph_tool_calls']}"
    )

    print(
        "Retrieved records: "
        f"{response['retrieved_record_count']}"
    )

    print(
        "Tool selection correct: "
        + (
            "YES"
            if evaluation[
                "tool_selection_correct"
            ]
            else "NO"
        )
    )

    print(
        "Tool call count correct: "
        + (
            "YES"
            if evaluation[
                "tool_call_count_correct"
            ]
            else "NO"
        )
    )

    print(
        "Tool execution success: "
        + (
            "YES"
            if evaluation[
                "tool_execution_success"
            ]
            else "NO"
        )
    )

    print(
        "Answer values complete: "
        + (
            "YES"
            if evaluation[
                "answer_values_complete"
            ]
            else "NO"
        )
    )

    if evaluation[
        "missing_answer_values"
    ]:
        print(
            "Missing answer values: "
            + ", ".join(
                evaluation[
                    "missing_answer_values"
                ]
            )
        )

    if result["expected"][
        "expectNoResultAnswer"
    ]:
        print(
            "No-result handling correct: "
            + (
                "YES"
                if evaluation[
                    "no_result_handling_correct"
                ]
                else "NO"
            )
        )

    print(
        "Fully correct: "
        + (
            "YES"
            if evaluation[
                "fully_correct"
            ]
            else "NO"
        )
    )

    print("Agent answer:")
    print(response["answer"])


def print_summary(
    summary: dict,
) -> None:
    total = summary["cases"]

    print()
    print("AGENT EVALUATION SUMMARY")

    print(
        "Execution: "
        f"{summary['executed']}/{total}"
    )

    print(
        "Fully correct: "
        f"{summary['fullyCorrect']}/{total}"
    )

    print(
        "Tool selection correct: "
        f"{summary['toolSelectionCorrect']}/{total}"
    )

    print(
        "Tool call count correct: "
        f"{summary['toolCallCountCorrect']}/{total}"
    )

    print(
        "Tool execution success: "
        f"{summary['toolExecutionSuccess']}/{total}"
    )

    print(
        "Answer values complete: "
        f"{summary['answerValuesComplete']}/{total}"
    )

    print(
        "No-result handling correct: "
        f"{summary['noResultHandlingCorrect']}/{total}"
    )


async def main():
    args = parse_args()

    benchmark = load_agent_benchmark(
        args.benchmark
    )

    cases = select_agent_cases(
        benchmark.cases,
        args.case,
    )

    print(
        f"Loaded {len(cases)} agent "
        "benchmark case(s) "
        f"(version {benchmark.version})."
    )

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
            f"Configured model: {llm.model}"
        )

        results = []

        for case in cases:
            result = await run_case(
                agent,
                case,
            )

            results.append(result)

            print_case_result(result)

        summary = build_summary(
            results
        )

        print_summary(summary)

        if args.output:
            output_path = Path(
                args.output
            )

            output_path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            payload = {
                "benchmarkVersion": (
                    benchmark.version
                ),
                "results": results,
                "summary": summary,
            }

            output_path.write_text(
                json.dumps(
                    payload,
                    indent=2,
                    default=str,
                ),
                encoding="utf-8",
            )

            print()
            print(
                "Structured results saved to: "
                f"{output_path}"
            )

    finally:
        neo4j.close()
        await llm.stop()


if __name__ == "__main__":
    asyncio.run(main())