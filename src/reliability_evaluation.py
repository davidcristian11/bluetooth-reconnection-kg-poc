from collections import Counter
import re

from evaluation import (
    EvaluationResult,
    classify_result,
)


def normalize_cypher(
    cypher: str | None,
) -> str | None:
    if cypher is None:
        return None

    return re.sub(
        r"\s+",
        " ",
        cypher,
    ).strip()


def percentage(
    numerator: int,
    denominator: int,
) -> float:
    if denominator == 0:
        return 0.0

    return round(
        numerator / denominator * 100,
        2,
    )


def build_reliability_summary(
    runs: list[list[EvaluationResult]],
) -> dict:
    all_results = [
        result
        for run in runs
        for result in run
    ]

    total_runs = len(runs)
    total_case_executions = len(all_results)

    fully_correct_executions = sum(
        classify_result(result)
        == "fully_correct"
        for result in all_results
    )

    executions_with_retry = sum(
        (
            result.generation_attempts is not None
            and result.generation_attempts > 1
        )
        for result in all_results
    )

    perfect_runs = sum(
        bool(run)
        and all(
            classify_result(result)
            == "fully_correct"
            for result in run
        )
        for run in runs
    )

    outcome_counts = Counter(
        classify_result(result)
        for result in all_results
    )

    retry_reason_counts = Counter(
        result.retry_reason
        for result in all_results
        if result.retry_reason
    )

    by_case = {}

    case_ids = sorted(
        {
            result.case_id
            for result in all_results
        }
    )

    for case_id in case_ids:
        case_results = [
            result
            for result in all_results
            if result.case_id == case_id
        ]

        correct_count = sum(
            classify_result(result)
            == "fully_correct"
            for result in case_results
        )

        retry_count = sum(
            (
                result.generation_attempts is not None
                and result.generation_attempts > 1
            )
            for result in case_results
        )

        normalized_cyphers = {
            normalize_cypher(result.cypher)
            for result in case_results
            if result.cypher
        }

        by_case[case_id] = {
            "category": case_results[0].category,
            "runs": len(case_results),
            "fully_correct": correct_count,
            "fully_correct_rate": percentage(
                correct_count,
                len(case_results),
            ),
            "retries": retry_count,
            "retry_rate": percentage(
                retry_count,
                len(case_results),
            ),
            "unique_cypher_count": len(
                normalized_cyphers
            ),
        }

    by_category = {}

    categories = sorted(
        {
            result.category
            for result in all_results
        }
    )

    for category in categories:
        category_results = [
            result
            for result in all_results
            if result.category == category
        ]

        correct_count = sum(
            classify_result(result)
            == "fully_correct"
            for result in category_results
        )

        retry_count = sum(
            (
                result.generation_attempts is not None
                and result.generation_attempts > 1
            )
            for result in category_results
        )

        by_category[category] = {
            "executions": len(category_results),
            "fully_correct": correct_count,
            "fully_correct_rate": percentage(
                correct_count,
                len(category_results),
            ),
            "retries": retry_count,
            "retry_rate": percentage(
                retry_count,
                len(category_results),
            ),
        }

    cases_with_cypher_variation = [
        case_id
        for case_id, metrics in by_case.items()
        if metrics["unique_cypher_count"] > 1
    ]

    return {
        "total_runs": total_runs,
        "total_case_executions": total_case_executions,
        "perfect_runs": perfect_runs,
        "perfect_run_rate": percentage(
            perfect_runs,
            total_runs,
        ),
        "fully_correct_executions": (
            fully_correct_executions
        ),
        "fully_correct_rate": percentage(
            fully_correct_executions,
            total_case_executions,
        ),
        "executions_with_retry": (
            executions_with_retry
        ),
        "retry_rate": percentage(
            executions_with_retry,
            total_case_executions,
        ),
        "outcomes": {
            "fully_correct": outcome_counts.get(
                "fully_correct",
                0,
            ),
            "execution_failure": outcome_counts.get(
                "execution_failure",
                0,
            ),
            "retrieval_failure": outcome_counts.get(
                "retrieval_failure",
                0,
            ),
            "answer_failure": outcome_counts.get(
                "answer_failure",
                0,
            ),
        },
        "retry_reasons": dict(
            sorted(
                retry_reason_counts.items()
            )
        ),
        "cases_with_cypher_variation": (
            cases_with_cypher_variation
        ),
        "by_case": by_case,
        "by_category": by_category,
    }