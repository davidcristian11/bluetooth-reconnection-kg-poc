from dataclasses import dataclass

from agent_benchmark import AgentBenchmarkCase
from agent_service import AgentResponse


NO_RESULT_MARKERS = (
    "no matching",
    "no information",
    "no graph facts",
    "no data",
    "no results",
    "not available",
    "could not find",
    "couldn't find",
    "nothing was found",
    "nothing found",
)


@dataclass(frozen=True)
class AgentEvaluation:
    tool_selection_correct: bool
    tool_call_count_correct: bool
    tool_execution_success: bool
    answer_values_complete: bool
    no_result_handling_correct: bool
    fully_correct: bool
    missing_answer_values: tuple[str, ...]


def _contains_value(
    answer: str,
    expected_value: str,
) -> bool:
    return (
        expected_value.casefold()
        in answer.casefold()
    )


def _missing_answer_values(
    case: AgentBenchmarkCase,
    answer: str,
) -> tuple[str, ...]:
    return tuple(
        value
        for value
        in case.expected.required_answer_values
        if not _contains_value(
            answer,
            value,
        )
    )


def _answer_indicates_no_result(
    answer: str,
) -> bool:
    normalized = answer.casefold()

    return any(
        marker in normalized
        for marker in NO_RESULT_MARKERS
    )


def evaluate_agent_response(
    case: AgentBenchmarkCase,
    response: AgentResponse,
) -> AgentEvaluation:
    expected = case.expected

    tool_selection_correct = (
        response.graph_tool_used
        == expected.graph_tool_required
    )

    if expected.graph_tool_required:
        tool_call_count_correct = (
            response.graph_tool_calls >= 1
            and response.graph_tool_calls
            <= expected.max_graph_tool_calls
        )

        tool_execution_success = (
            response.graph_tool_successes >= 1
            and response.tool_error is None
        )

    else:
        tool_call_count_correct = (
            response.graph_tool_calls == 0
        )

        tool_execution_success = (
            response.graph_tool_successes == 0
            and response.tool_error is None
        )

    missing_values = _missing_answer_values(
        case,
        response.answer,
    )

    answer_values_complete = (
        len(missing_values) == 0
    )

    if expected.expect_no_result_answer:
        no_result_handling_correct = (
            response.retrieved_record_count == 0
            and _answer_indicates_no_result(
                response.answer
            )
        )
    else:
        no_result_handling_correct = True

    fully_correct = all(
        (
            tool_selection_correct,
            tool_call_count_correct,
            tool_execution_success,
            answer_values_complete,
            no_result_handling_correct,
        )
    )

    return AgentEvaluation(
        tool_selection_correct=(
            tool_selection_correct
        ),
        tool_call_count_correct=(
            tool_call_count_correct
        ),
        tool_execution_success=(
            tool_execution_success
        ),
        answer_values_complete=(
            answer_values_complete
        ),
        no_result_handling_correct=(
            no_result_handling_correct
        ),
        fully_correct=fully_correct,
        missing_answer_values=(
            missing_values
        ),
    )