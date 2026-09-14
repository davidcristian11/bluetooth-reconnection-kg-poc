import argparse
import asyncio
import json
from pathlib import Path

from flat_retriever import (
    LexicalFlatRetriever,
)
from llm_client import LLMClient
from neo4j_client import Neo4jClient
from query_service import QueryService
from retrieval_benchmark import (
    load_retrieval_benchmark,
)
from retrieval_evaluation import (
    evaluate_retrieved_evidence,
    flat_results_to_records,
)


PROJECT_ROOT = Path(
    __file__
).resolve().parents[1]

DEFAULT_BENCHMARK = (
    PROJECT_ROOT
    / "evaluation"
    / "retrieval_benchmark.yaml"
)


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Compare the deterministic flat "
            "lexical retriever with the current "
            "schema-guided Neo4j graph retriever."
        )
    )

    parser.add_argument(
        "--benchmark",
        type=Path,
        default=DEFAULT_BENCHMARK,
        help=(
            "Path to the retrieval benchmark "
            "YAML file."
        ),
    )

    parser.add_argument(
        "--case",
        dest="case_id",
        help=(
            "Optional benchmark case ID to run "
            "instead of the full benchmark."
        ),
    )

    parser.add_argument(
        "--output",
        type=Path,
        help=(
            "Optional path for structured "
            "JSON results."
        ),
    )

    parser.add_argument(
        "--show-cypher",
        action="store_true",
        help=(
            "Print generated Cypher for graph "
            "retrieval cases."
        ),
    )

    return parser.parse_args()


def _metrics_to_dict(
    metrics,
) -> dict:
    return {
        "recall": metrics.recall,
        "precision": metrics.precision,
        "evidence_complete": (
            metrics.evidence_complete
        ),
        "expected_atoms": list(
            metrics.expected_atoms
        ),
        "matched_atoms": list(
            metrics.matched_atoms
        ),
        "missing_atoms": list(
            metrics.missing_atoms
        ),
        "unexpected_atoms": list(
            metrics.unexpected_atoms
        ),
    }


def run_flat_case(
    retriever: LexicalFlatRetriever,
    case,
) -> dict:
    results = retriever.search(
        case.question,
        top_k=case.top_k,
    )

    records = flat_results_to_records(
        results
    )

    metrics = evaluate_retrieved_evidence(
        records,
        case.expected,
    )

    return {
        "execution_success": True,
        "retrieved_count": len(records),
        "metrics": _metrics_to_dict(
            metrics
        ),
        "records": records,
        "error": None,
    }


async def run_graph_case(
    service: QueryService,
    case,
) -> dict:
    try:
        response = (
            await service.retrieve_question(
                case.question
            )
        )

        metrics = (
            evaluate_retrieved_evidence(
                response.records,
                case.expected,
            )
        )

        return {
            "execution_success": True,
            "retrieved_count": len(
                response.records
            ),
            "metrics": _metrics_to_dict(
                metrics
            ),
            "records": response.records,
            "cypher": response.cypher,
            "generation_attempts": (
                response.generation_attempts
            ),
            "retry_reason": (
                response.retry_reason
            ),
            "error": None,
        }

    except Exception as error:
        return {
            "execution_success": False,
            "retrieved_count": 0,
            "metrics": {
                "recall": 0.0,
                "precision": 0.0,
                "evidence_complete": False,
                "expected_atoms": [],
                "matched_atoms": [],
                "missing_atoms": [],
                "unexpected_atoms": [],
            },
            "records": [],
            "cypher": None,
            "generation_attempts": None,
            "retry_reason": None,
            "error": str(error),
        }


def _strategy_summary(
    results: list[dict],
    strategy: str,
) -> dict:
    total = len(results)

    successful = sum(
        1
        for result in results
        if result[strategy][
            "execution_success"
        ]
    )

    complete = sum(
        1
        for result in results
        if result[strategy]["metrics"][
            "evidence_complete"
        ]
    )

    mean_recall = sum(
        result[strategy]["metrics"][
            "recall"
        ]
        for result in results
    ) / total

    mean_precision = sum(
        result[strategy]["metrics"][
            "precision"
        ]
        for result in results
    ) / total

    return {
        "total_cases": total,
        "execution_success": successful,
        "evidence_complete": complete,
        "mean_recall": mean_recall,
        "mean_precision": mean_precision,
    }


def build_summary(
    results: list[dict],
) -> dict:
    categories = sorted(
        {
            result["category"]
            for result in results
        }
    )

    by_category = {}

    for category in categories:
        category_results = [
            result
            for result in results
            if result["category"]
            == category
        ]

        by_category[category] = {
            "flat": _strategy_summary(
                category_results,
                "flat",
            ),
            "graph": _strategy_summary(
                category_results,
                "graph",
            ),
        }

    return {
        "flat": _strategy_summary(
            results,
            "flat",
        ),
        "graph": _strategy_summary(
            results,
            "graph",
        ),
        "by_category": by_category,
    }


def _status(
    value: bool,
) -> str:
    return (
        "YES"
        if value
        else "NO"
    )


def print_case_result(
    result: dict,
    *,
    show_cypher: bool,
) -> None:
    print(
        f"\n[{result['case_id']}] "
        f"{result['category']}"
    )

    print(
        f"Question: "
        f"{result['question']}"
    )

    for strategy in (
        "flat",
        "graph",
    ):
        strategy_result = (
            result[strategy]
        )

        metrics = (
            strategy_result["metrics"]
        )

        print(
            f"{strategy.capitalize()}: "
            f"recall="
            f"{metrics['recall']:.3f}, "
            f"precision="
            f"{metrics['precision']:.3f}, "
            "evidence_complete="
            f"{_status(metrics['evidence_complete'])}, "
            f"retrieved="
            f"{strategy_result['retrieved_count']}"
        )

        if metrics["missing_atoms"]:
            print(
                "  Missing: "
                f"{', '.join(metrics['missing_atoms'])}"
            )

        if metrics["unexpected_atoms"]:
            print(
                "  Unexpected: "
                f"{', '.join(metrics['unexpected_atoms'])}"
            )

        if strategy_result.get(
            "error"
        ):
            print(
                "  Error: "
                f"{strategy_result['error']}"
            )

    graph_result = result["graph"]

    if (
        graph_result.get(
            "generation_attempts"
        )
        is not None
    ):
        print(
            "Graph Cypher attempts: "
            f"{graph_result['generation_attempts']}"
        )

    if graph_result.get(
        "retry_reason"
    ):
        print(
            "Graph retry reason: "
            f"{graph_result['retry_reason']}"
        )

    if (
        show_cypher
        and graph_result.get("cypher")
    ):
        print("Graph Cypher:")
        print(graph_result["cypher"])


def print_summary(
    summary: dict,
) -> None:
    print(
        "\nRETRIEVAL EXPERIMENT SUMMARY"
    )

    for strategy in (
        "flat",
        "graph",
    ):
        metrics = summary[strategy]

        print(
            f"{strategy.capitalize()}: "
            f"execution="
            f"{metrics['execution_success']}/"
            f"{metrics['total_cases']}, "
            f"complete="
            f"{metrics['evidence_complete']}/"
            f"{metrics['total_cases']}, "
            f"mean_recall="
            f"{metrics['mean_recall']:.3f}, "
            f"mean_precision="
            f"{metrics['mean_precision']:.3f}"
        )

    print("\nBY CATEGORY")

    for category, strategies in (
        summary["by_category"].items()
    ):
        flat = strategies["flat"]
        graph = strategies["graph"]

        print(
            f"{category}: "
            "flat("
            f"recall="
            f"{flat['mean_recall']:.3f}, "
            f"precision="
            f"{flat['mean_precision']:.3f}, "
            f"complete="
            f"{flat['evidence_complete']}/"
            f"{flat['total_cases']}) | "
            "graph("
            f"recall="
            f"{graph['mean_recall']:.3f}, "
            f"precision="
            f"{graph['mean_precision']:.3f}, "
            f"complete="
            f"{graph['evidence_complete']}/"
            f"{graph['total_cases']})"
        )


def write_results(
    path: Path,
    *,
    benchmark_version: int,
    configured_model: str,
    results: list[dict],
    summary: dict,
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    payload = {
        "benchmark_version": (
            benchmark_version
        ),
        "configured_model": (
            configured_model
        ),
        "results": results,
        "summary": summary,
    }

    path.write_text(
        json.dumps(
            payload,
            indent=2,
            default=str,
        ),
        encoding="utf-8",
    )


async def main() -> int:
    args = parse_args()

    benchmark_version, cases = (
        load_retrieval_benchmark(
            args.benchmark
        )
    )

    if args.case_id:
        cases = [
            case
            for case in cases
            if case.id == args.case_id
        ]

        if not cases:
            raise ValueError(
                "Unknown retrieval benchmark "
                f"case: {args.case_id}"
            )

    flat_retriever = (
        LexicalFlatRetriever.from_project_data(
            PROJECT_ROOT
        )
    )

    llm = LLMClient()
    neo4j = Neo4jClient()

    await llm.start()

    try:
        neo4j.verify_connection()

        graph_service = QueryService(
            llm_client=llm,
            neo4j_client=neo4j,
        )

        print(
            f"Loaded {len(cases)} retrieval "
            f"benchmark case(s) "
            f"(version {benchmark_version})."
        )

        print(
            f"Loaded "
            f"{len(flat_retriever.documents)} "
            "flat documents."
        )

        print(
            f"Configured model: "
            f"{llm.model}"
        )

        print(
            "Graph mode: retrieval only "
            "(final-answer generation disabled)."
        )

        results = []

        for case in cases:
            flat_result = run_flat_case(
                flat_retriever,
                case,
            )

            graph_result = (
                await run_graph_case(
                    graph_service,
                    case,
                )
            )

            result = {
                "case_id": case.id,
                "category": case.category,
                "question": case.question,
                "top_k": case.top_k,
                "flat": flat_result,
                "graph": graph_result,
            }

            results.append(result)

            print_case_result(
                result,
                show_cypher=(
                    args.show_cypher
                ),
            )

        summary = build_summary(
            results
        )

        print_summary(summary)

        if args.output:
            write_results(
                args.output,
                benchmark_version=(
                    benchmark_version
                ),
                configured_model=llm.model,
                results=results,
                summary=summary,
            )

            print(
                "\nStructured results "
                "written to: "
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