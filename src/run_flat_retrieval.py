import argparse
from pathlib import Path

from flat_retriever import LexicalFlatRetriever
from retrieval_benchmark import load_retrieval_benchmark


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DEFAULT_BENCHMARK = (
    PROJECT_ROOT
    / "evaluation"
    / "retrieval_benchmark.yaml"
)


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Run the deterministic flat lexical retrieval baseline "
            "against the retrieval benchmark."
        )
    )

    parser.add_argument(
        "--benchmark",
        type=Path,
        default=DEFAULT_BENCHMARK,
        help="Path to the retrieval benchmark YAML file.",
    )

    return parser.parse_args()


def print_case_results(
    case,
    results,
) -> None:
    print(f"\n[{case.id}] {case.category}")
    print(f"Question: {case.question}")
    print(f"Top-K: {case.top_k}")

    if not results:
        print("No lexical matches.")
        return

    for rank, result in enumerate(results, start=1):
        print(
            f"{rank:>2}. "
            f"score={result.score:.4f} "
            f"{result.document.document_id}"
        )
        print(f"    {result.document.text}")


def main() -> int:
    args = parse_args()

    benchmark_version, cases = load_retrieval_benchmark(
        args.benchmark
    )

    retriever = LexicalFlatRetriever.from_project_data(
        PROJECT_ROOT
    )

    print(
        f"Loaded {len(retriever.documents)} flat documents "
        f"from the synthetic source data."
    )

    print(
        f"Loaded {len(cases)} retrieval benchmark cases "
        f"(version {benchmark_version})."
    )

    for case in cases:
        results = retriever.search(
            case.question,
            top_k=case.top_k,
        )

        print_case_results(
            case,
            results,
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())