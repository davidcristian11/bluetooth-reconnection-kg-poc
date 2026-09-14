from dataclasses import dataclass
from pathlib import Path

import yaml


DEFAULT_AGENT_BENCHMARK_PATH = Path(
    "evaluation/agent_benchmark.yaml"
)

SUPPORTED_AGENT_CATEGORIES = {
    "direct_relationship",
    "multi_hop",
    "filtering",
    "cross_environment",
    "no_result",
    "conceptual",
    "capability",
    "conversational",
}


@dataclass(frozen=True)
class AgentBenchmarkExpected:
    graph_tool_required: bool
    max_graph_tool_calls: int
    required_answer_values: tuple[str, ...]
    expect_no_result_answer: bool


@dataclass(frozen=True)
class AgentBenchmarkCase:
    id: str
    category: str
    question: str
    expected: AgentBenchmarkExpected


@dataclass(frozen=True)
class AgentBenchmark:
    version: int
    cases: tuple[AgentBenchmarkCase, ...]


def _require_non_empty_string(
    value,
    field_name: str,
) -> str:
    if (
        not isinstance(value, str)
        or not value.strip()
    ):
        raise ValueError(
            f"{field_name} must be a non-empty string."
        )

    return value.strip()


def _parse_required_answer_values(
    value,
    case_id: str,
) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise ValueError(
            f"{case_id}: requiredAnswerValues "
            "must be a list."
        )

    values = []

    for item in value:
        if (
            not isinstance(item, str)
            or not item.strip()
        ):
            raise ValueError(
                f"{case_id}: requiredAnswerValues "
                "must contain only non-empty strings."
            )

        values.append(item.strip())

    if len(values) != len(set(values)):
        raise ValueError(
            f"{case_id}: requiredAnswerValues "
            "must not contain duplicates."
        )

    return tuple(values)


def _parse_expected(
    raw_expected,
    case_id: str,
) -> AgentBenchmarkExpected:
    if not isinstance(raw_expected, dict):
        raise ValueError(
            f"{case_id}: expected must be an object."
        )

    graph_tool_required = raw_expected.get(
        "graphToolRequired"
    )

    if not isinstance(
        graph_tool_required,
        bool,
    ):
        raise ValueError(
            f"{case_id}: graphToolRequired "
            "must be a boolean."
        )

    max_graph_tool_calls = raw_expected.get(
        "maxGraphToolCalls"
    )

    if (
        not isinstance(
            max_graph_tool_calls,
            int,
        )
        or isinstance(
            max_graph_tool_calls,
            bool,
        )
        or max_graph_tool_calls < 0
    ):
        raise ValueError(
            f"{case_id}: maxGraphToolCalls "
            "must be a non-negative integer."
        )

    if (
        graph_tool_required
        and max_graph_tool_calls < 1
    ):
        raise ValueError(
            f"{case_id}: graphToolRequired=true "
            "requires maxGraphToolCalls >= 1."
        )

    if (
        not graph_tool_required
        and max_graph_tool_calls != 0
    ):
        raise ValueError(
            f"{case_id}: graphToolRequired=false "
            "requires maxGraphToolCalls=0."
        )

    required_answer_values = (
        _parse_required_answer_values(
            raw_expected.get(
                "requiredAnswerValues"
            ),
            case_id,
        )
    )

    expect_no_result_answer = (
        raw_expected.get(
            "expectNoResultAnswer",
            False,
        )
    )

    if not isinstance(
        expect_no_result_answer,
        bool,
    ):
        raise ValueError(
            f"{case_id}: expectNoResultAnswer "
            "must be a boolean."
        )

    if (
        expect_no_result_answer
        and not graph_tool_required
    ):
        raise ValueError(
            f"{case_id}: expectNoResultAnswer=true "
            "requires graphToolRequired=true."
        )

    return AgentBenchmarkExpected(
        graph_tool_required=(
            graph_tool_required
        ),
        max_graph_tool_calls=(
            max_graph_tool_calls
        ),
        required_answer_values=(
            required_answer_values
        ),
        expect_no_result_answer=(
            expect_no_result_answer
        ),
    )


def load_agent_benchmark(
    path: str | Path = (
        DEFAULT_AGENT_BENCHMARK_PATH
    ),
) -> AgentBenchmark:
    benchmark_path = Path(path)

    with benchmark_path.open(
        "r",
        encoding="utf-8",
    ) as file:
        raw = yaml.safe_load(file)

    if not isinstance(raw, dict):
        raise ValueError(
            "Agent benchmark root "
            "must be an object."
        )

    version = raw.get("version")

    if (
        not isinstance(version, int)
        or isinstance(version, bool)
        or version < 1
    ):
        raise ValueError(
            "Agent benchmark version "
            "must be a positive integer."
        )

    raw_cases = raw.get("cases")

    if (
        not isinstance(raw_cases, list)
        or not raw_cases
    ):
        raise ValueError(
            "Agent benchmark must contain "
            "at least one case."
        )

    cases = []
    seen_ids = set()

    for index, raw_case in enumerate(
        raw_cases,
        start=1,
    ):
        if not isinstance(raw_case, dict):
            raise ValueError(
                "Each agent benchmark case "
                "must be an object."
            )

        case_id = _require_non_empty_string(
            raw_case.get("id"),
            f"cases[{index}].id",
        )

        if case_id in seen_ids:
            raise ValueError(
                f"Duplicate agent benchmark "
                f"case id: {case_id}"
            )

        seen_ids.add(case_id)

        category = _require_non_empty_string(
            raw_case.get("category"),
            f"{case_id}.category",
        )

        if (
            category
            not in SUPPORTED_AGENT_CATEGORIES
        ):
            raise ValueError(
                f"{case_id}: unsupported category "
                f"'{category}'."
            )

        question = _require_non_empty_string(
            raw_case.get("question"),
            f"{case_id}.question",
        )

        expected = _parse_expected(
            raw_case.get("expected"),
            case_id,
        )

        cases.append(
            AgentBenchmarkCase(
                id=case_id,
                category=category,
                question=question,
                expected=expected,
            )
        )

    return AgentBenchmark(
        version=version,
        cases=tuple(cases),
    )