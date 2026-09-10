import argparse
import asyncio
import json
from pathlib import Path

from evaluation import (
    build_summary,
    load_benchmark,
)
from llm_client import LLMClient
from neo4j_client import Neo4jClient
from query_service import QueryService
from reliability_evaluation import (
    build_reliability_summary,
)
from run_evaluation import run_case


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DEFAULT_BENCHMARK = (
    PROJECT_ROOT
    / "evaluation"
    / "benchmark.yaml"
)


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Run the AI benchmark repeatedly and measure "
            "pipeline reliability across runs."
        )
    )

    parser.add_argument(
        "--benchmark",
        type=Path,
        default=DEFAULT_BENCHMARK,
        help="Path to the benchmark YAML file.",
    )

    parser.add_argument(
        "--runs",
        type=int,
        default=5,
        help=(
            "Number of complete benchmark runs. "
            "Default: 5."
        ),
    )

    parser.add_argument(
        "--output",
        type=Path,
        help=(
            "Optional JSON output path for detailed "
            "reliability results."
        ),
    )

    return parser.parse_args()


def print_run_summary(
    run_number: int,
    total_runs: int,
    summary: dict,
) -> None:
    total = summary["total_cases"]

    print(
        f"\nRUN {run_number}/{total_runs} SUMMARY"
    )

    print(
        "Fully correct: "
        f"{summary['fully_correct']}/{total}"
    )

    print(
        "Execution: "
        f"{summary['execution_success']}/{total}"
    )

    print(
        "Retrieval: "
        f"{summary['retrieval_correct']}/{total}"
    )

    print(
        "Answer: "
        f"{summary['answer_correct']}/{total}"
    )


def print_reliability_summary(
    summary: dict,
) -> None:
    print("\nRELIABILITY SUMMARY")

    print(
        "Runs: "
        f"{summary['total_runs']}"
    )

    print(
        "Case executions: "
        f"{summary['total_case_executions']}"
    )

    print(
        "Perfect runs: "
        f"{summary['perfect_runs']}/"
        f"{summary['total_runs']} "
        f"({summary['perfect_run_rate']}%)"
    )

    print(
        "Fully correct executions: "
        f"{summary['fully_correct_executions']}/"
        f"{summary['total_case_executions']} "
        f"({summary['fully_correct_rate']}%)"
    )

    print(
        "Executions requiring retry: "
        f"{summary['executions_with_retry']}/"
        f"{summary['total_case_executions']} "
        f"({summary['retry_rate']}%)"
    )

    print("\nOUTCOMES")

    for outcome, count in (
        summary["outcomes"].items()
    ):
        print(
            f"{outcome}: {count}"
        )

    print("\nRETRY REASONS")

    if summary["retry_reasons"]:
        for reason, count in (
            summary["retry_reasons"].items()
        ):
            print(
                f"{reason}: {count}"
            )
    else:
        print("none")

    print("\nCYPHER VARIATION")

    variation = (
        summary[
            "cases_with_cypher_variation"
        ]
    )

    if variation:
        print(
            "Cases with more than one "
            "generated Cypher shape:"
        )

        for case_id in variation:
            unique_count = (
                summary["by_case"][case_id][
                    "unique_cypher_count"
                ]
            )

            print(
                f"{case_id}: "
                f"{unique_count} unique queries"
            )
    else:
        print(
            "No Cypher variation observed."
        )

    print("\nBY CASE")

    for case_id, metrics in (
        summary["by_case"].items()
    ):
        print(
            f"{case_id}: "
            f"correct="
            f"{metrics['fully_correct']}/"
            f"{metrics['runs']} "
            f"({metrics['fully_correct_rate']}%), "
            f"retries={metrics['retries']}, "
            f"unique_cypher="
            f"{metrics['unique_cypher_count']}"
        )


async def main() -> int:
    args = parse_args()

    if args.runs <= 0:
        raise ValueError(
            "--runs must be greater than zero."
        )

    benchmark_version, cases = load_benchmark(
        args.benchmark
    )

    llm = LLMClient()
    neo4j = Neo4jClient()

    await llm.start()

    all_runs = []

    try:
        neo4j.verify_connection()

        service = QueryService(
            llm_client=llm,
            neo4j_client=neo4j,
        )

        print(
            f"Benchmark version: "
            f"{benchmark_version}"
        )

        print(
            f"Configured model: {llm.model}"
        )

        print(
            f"Cases per run: {len(cases)}"
        )

        print(
            f"Requested runs: {args.runs}"
        )

        for run_number in range(
            1,
            args.runs + 1,
        ):
            print(
                f"\n=== RUN "
                f"{run_number}/{args.runs} ==="
            )

            run_results = []

            for case in cases:
                result = await run_case(
                    service,
                    case,
                )

                run_results.append(result)

                status = (
                    "PASS"
                    if (
                        result.execution_success
                        and result.retrieval_correct
                        and result.answer_correct
                    )
                    else "FAIL"
                )

                retry_note = ""

                if (
                    result.generation_attempts
                    and result.generation_attempts > 1
                ):
                    retry_note = (
                        " "
                        f"[retry="
                        f"{result.retry_reason}]"
                    )

                print(
                    f"{result.case_id}: "
                    f"{status}"
                    f"{retry_note}"
                )

                if result.error:
                    print(
                        f"  Error: "
                        f"{result.error}"
                    )

                for issue in (
                    result.retrieval_issues
                ):
                    print(
                        f"  Retrieval: {issue}"
                    )

                for issue in (
                    result.answer_issues
                ):
                    print(
                        f"  Answer: {issue}"
                    )

            all_runs.append(run_results)

            print_run_summary(
                run_number,
                args.runs,
                build_summary(run_results),
            )

        reliability_summary = (
            build_reliability_summary(
                all_runs
            )
        )

        print_reliability_summary(
            reliability_summary
        )

        if args.output:
            payload = {
                "benchmark_version": (
                    benchmark_version
                ),
                "configured_model": llm.model,
                "summary": reliability_summary,
                "runs": [
                    {
                        "run": index,
                        "summary": build_summary(
                            results
                        ),
                        "results": [
                            result.to_dict()
                            for result in results
                        ],
                    }
                    for index, results in enumerate(
                        all_runs,
                        start=1,
                    )
                ],
            }

            args.output.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            args.output.write_text(
                json.dumps(
                    payload,
                    indent=2,
                    default=str,
                )
                + "\n",
                encoding="utf-8",
            )

            print(
                "\nStructured reliability "
                "results written to: "
                f"{args.output}"
            )

        return 0

    finally:
        neo4j.close()
        await llm.stop()


if __name__ == "__main__":
    raise SystemExit(
        asyncio.run(main())
    )