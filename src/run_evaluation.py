import argparse
import asyncio
from pathlib import Path

from evaluation import (
    EvaluationResult,
    build_summary,
    evaluate_answer,
    evaluate_retrieval,
    load_benchmark,
    write_results,
)
from llm_client import LLMClient
from neo4j_client import Neo4jClient
from query_service import QueryService


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DEFAULT_BENCHMARK = (
    PROJECT_ROOT
    / "evaluation"
    / "benchmark.yaml"
)


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Run the AI evaluation benchmark against "
            "the current schema-guided Text-to-Cypher pipeline."
        )
    )

    parser.add_argument(
        "--benchmark",
        type=Path,
        default=DEFAULT_BENCHMARK,
        help="Path to the benchmark YAML file.",
    )

    parser.add_argument(
        "--output",
        type=Path,
        help=(
            "Optional path for structured JSON results."
        ),
    )

    return parser.parse_args()


async def run_case(
    service: QueryService,
    case,
) -> EvaluationResult:
    try:
        response = await service.answer_question(
            case.question
        )

        (
            retrieval_correct,
            retrieval_issues,
        ) = evaluate_retrieval(
            response.records,
            case.expected,
        )

        (
            answer_correct,
            answer_issues,
        ) = evaluate_answer(
            response.answer,
            case.expected,
        )

        return EvaluationResult(
            case_id=case.id,
            category=case.category,
            question=case.question,
            execution_success=True,
            retrieval_correct=retrieval_correct,
            answer_correct=answer_correct,
            generation_attempts=(
                response.generation_attempts
            ),
            cypher=response.cypher,
            records=response.records,
            answer=response.answer,
            retrieval_issues=retrieval_issues,
            answer_issues=answer_issues,
            error=None,
        )

    except Exception as error:
        return EvaluationResult(
            case_id=case.id,
            category=case.category,
            question=case.question,
            execution_success=False,
            retrieval_correct=False,
            answer_correct=False,
            generation_attempts=None,
            cypher=None,
            records=[],
            answer=None,
            retrieval_issues=[],
            answer_issues=[],
            error=str(error),
        )


def print_result(
    result: EvaluationResult,
) -> None:
    def status(value: bool) -> str:
        return "PASS" if value else "FAIL"

    print(
        f"\n[{result.case_id}] "
        f"{result.category}"
    )

    print(f"Question: {result.question}")

    print(
        "Execution: "
        f"{status(result.execution_success)}"
    )

    print(
        "Retrieval: "
        f"{status(result.retrieval_correct)}"
    )

    print(
        "Answer: "
        f"{status(result.answer_correct)}"
    )

    if result.generation_attempts is not None:
        print(
            "Cypher attempts: "
            f"{result.generation_attempts}"
        )

    for issue in result.retrieval_issues:
        print(f"Retrieval issue: {issue}")

    for issue in result.answer_issues:
        print(f"Answer issue: {issue}")

    if result.error:
        print(f"Error: {result.error}")


def print_summary(
    summary: dict,
) -> None:
    total = summary["total_cases"]

    print("\nEVALUATION SUMMARY")

    print(
        "Execution success: "
        f"{summary['execution_success']}/{total}"
    )

    print(
        "Retrieval correct: "
        f"{summary['retrieval_correct']}/{total}"
    )

    print(
        "Answer correct: "
        f"{summary['answer_correct']}/{total}"
    )

    print(
        "Fully correct: "
        f"{summary['fully_correct']}/{total}"
    )

    print("\nOUTCOME BREAKDOWN")

    for outcome, count in summary["outcomes"].items():
        print(f"{outcome}: {count}")

    print("\nBY CATEGORY")

    for category, metrics in (
        summary["by_category"].items()
    ):
        print(
            f"{category}: "
            f"execution="
            f"{metrics['execution_success']}/"
            f"{metrics['total']}, "
            f"retrieval="
            f"{metrics['retrieval_correct']}/"
            f"{metrics['total']}, "
            f"answer="
            f"{metrics['answer_correct']}/"
            f"{metrics['total']}"
        )


async def main() -> int:
    args = parse_args()

    benchmark_version, cases = load_benchmark(
        args.benchmark
    )

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
            f"Loaded {len(cases)} benchmark cases "
            f"(version {benchmark_version})."
        )

        print(
            f"Configured model: {llm.model}"
        )

        results = []

        for case in cases:
            result = await run_case(
                service,
                case,
            )

            results.append(result)
            print_result(result)

        summary = build_summary(results)

        print_summary(summary)

        if args.output:
            write_results(
                args.output,
                benchmark_version=benchmark_version,
                configured_model=llm.model,
                results=results,
            )

            print(
                "\nStructured results written to: "
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