from agent_benchmark import (
    AgentBenchmarkCase,
    AgentBenchmarkExpected,
)
from agent_evaluation import (
    evaluate_agent_response,
)
from agent_service import AgentResponse


def make_case(
    *,
    graph_tool_required=True,
    max_graph_tool_calls=1,
    required_answer_values=(),
    expect_no_result_answer=False,
):
    return AgentBenchmarkCase(
        id="AGT-TEST",
        category="filtering",
        question="Test question",
        expected=AgentBenchmarkExpected(
            graph_tool_required=(
                graph_tool_required
            ),
            max_graph_tool_calls=(
                max_graph_tool_calls
            ),
            required_answer_values=(
                tuple(required_answer_values)
            ),
            expect_no_result_answer=(
                expect_no_result_answer
            ),
        ),
    )


def make_response(
    *,
    answer="",
    graph_tool_used=True,
    graph_tool_calls=1,
    graph_tool_successes=1,
    retrieved_record_count=1,
    tool_error=None,
):
    return AgentResponse(
        question="Test question",
        answer=answer,
        graph_tool_used=graph_tool_used,
        graph_tool_calls=graph_tool_calls,
        graph_tool_successes=(
            graph_tool_successes
        ),
        retrieved_record_count=(
            retrieved_record_count
        ),
        cypher_generation_attempts=1,
        retry_reason=None,
        tool_error=tool_error,
    )


def test_correct_graph_response_is_fully_correct():
    case = make_case(
        required_answer_values=(
            "REQ-002",
            "EXEC-010",
        )
    )

    response = make_response(
        answer=(
            "EXEC-010 is associated "
            "with REQ-002."
        )
    )

    evaluation = evaluate_agent_response(
        case,
        response,
    )

    assert evaluation.fully_correct is True
    assert (
        evaluation.missing_answer_values
        == ()
    )


def test_detects_wrong_tool_selection():
    case = make_case()

    response = make_response(
        graph_tool_used=False,
        graph_tool_calls=0,
        graph_tool_successes=0,
    )

    evaluation = evaluate_agent_response(
        case,
        response,
    )

    assert (
        evaluation.tool_selection_correct
        is False
    )

    assert evaluation.fully_correct is False


def test_detects_too_many_tool_calls():
    case = make_case()

    response = make_response(
        graph_tool_calls=2,
    )

    evaluation = evaluate_agent_response(
        case,
        response,
    )

    assert (
        evaluation.tool_call_count_correct
        is False
    )

    assert evaluation.fully_correct is False


def test_detects_missing_answer_value():
    case = make_case(
        required_answer_values=(
            "DEF-001",
            "Vehicle",
        )
    )

    response = make_response(
        answer="The linked defect is DEF-001."
    )

    evaluation = evaluate_agent_response(
        case,
        response,
    )

    assert (
        evaluation.answer_values_complete
        is False
    )

    assert (
        evaluation.missing_answer_values
        == ("Vehicle",)
    )


def test_accepts_valid_no_result_answer():
    case = make_case(
        required_answer_values=(),
        expect_no_result_answer=True,
    )

    response = make_response(
        answer=(
            "No matching graph facts were "
            "retrieved for REQ-999."
        ),
        retrieved_record_count=0,
    )

    evaluation = evaluate_agent_response(
        case,
        response,
    )

    assert (
        evaluation.no_result_handling_correct
        is True
    )

    assert evaluation.fully_correct is True


def test_rejects_bad_no_result_answer():
    case = make_case(
        required_answer_values=(),
        expect_no_result_answer=True,
    )

    response = make_response(
        answer=(
            "REQ-999 is an approved requirement."
        ),
        retrieved_record_count=0,
    )

    evaluation = evaluate_agent_response(
        case,
        response,
    )

    assert (
        evaluation.no_result_handling_correct
        is False
    )

    assert evaluation.fully_correct is False


def test_accepts_no_results_wording():
    case = make_case(
        required_answer_values=(),
        expect_no_result_answer=True,
    )

    response = make_response(
        answer=(
            "No results were retrieved "
            "for REQ-999."
        ),
        retrieved_record_count=0,
    )

    evaluation = evaluate_agent_response(
        case,
        response,
    )

    assert (
        evaluation.no_result_handling_correct
        is True
    )

    assert evaluation.fully_correct is True