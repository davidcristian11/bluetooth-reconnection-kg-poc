import pytest

from agent_benchmark import (
    AgentBenchmarkCase,
    AgentBenchmarkExpected,
)
from run_agent_evaluation import (
    build_summary,
    select_agent_cases,
)


def make_case(case_id):
    return AgentBenchmarkCase(
        id=case_id,
        category="conversational",
        question="Hello",
        expected=AgentBenchmarkExpected(
            graph_tool_required=False,
            max_graph_tool_calls=0,
            required_answer_values=(),
            expect_no_result_answer=False,
        ),
    )


def test_selects_all_cases_when_no_id():
    cases = (
        make_case("AGT-001"),
        make_case("AGT-002"),
    )

    selected = select_agent_cases(
        cases,
        None,
    )

    assert selected == cases


def test_selects_requested_case():
    cases = (
        make_case("AGT-001"),
        make_case("AGT-002"),
    )

    selected = select_agent_cases(
        cases,
        "AGT-002",
    )

    assert len(selected) == 1
    assert selected[0].id == "AGT-002"


def test_rejects_unknown_case():
    cases = (
        make_case("AGT-001"),
    )

    with pytest.raises(
        ValueError,
        match="Unknown agent benchmark case",
    ):
        select_agent_cases(
            cases,
            "AGT-999",
        )


def test_builds_agent_summary():
    results = [
        {
            "error": None,
            "evaluation": {
                "fully_correct": True,
                "tool_selection_correct": True,
                "tool_call_count_correct": True,
                "tool_execution_success": True,
                "answer_values_complete": True,
                "no_result_handling_correct": True,
            },
        },
        {
            "error": None,
            "evaluation": {
                "fully_correct": False,
                "tool_selection_correct": True,
                "tool_call_count_correct": True,
                "tool_execution_success": True,
                "answer_values_complete": False,
                "no_result_handling_correct": True,
            },
        },
    ]

    summary = build_summary(
        results
    )

    assert summary["cases"] == 2
    assert summary["executed"] == 2
    assert summary["fullyCorrect"] == 1

    assert (
        summary["toolSelectionCorrect"]
        == 2
    )

    assert (
        summary["answerValuesComplete"]
        == 1
    )