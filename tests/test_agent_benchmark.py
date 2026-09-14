from pathlib import Path

import pytest

from agent_benchmark import (
    SUPPORTED_AGENT_CATEGORIES,
    load_agent_benchmark,
)


def test_loads_default_agent_benchmark():
    benchmark = load_agent_benchmark()

    assert benchmark.version == 1
    assert len(benchmark.cases) == 8

    assert benchmark.cases[0].id == (
        "AGT-001"
    )

    assert benchmark.cases[-1].id == (
        "AGT-008"
    )


def test_default_benchmark_covers_categories():
    benchmark = load_agent_benchmark()

    categories = {
        case.category
        for case in benchmark.cases
    }

    assert categories == (
        SUPPORTED_AGENT_CATEGORIES
    )


def test_default_benchmark_has_expected_tool_split():
    benchmark = load_agent_benchmark()

    graph_cases = [
        case
        for case in benchmark.cases
        if case.expected.graph_tool_required
    ]

    direct_cases = [
        case
        for case in benchmark.cases
        if not case.expected.graph_tool_required
    ]

    assert len(graph_cases) == 5
    assert len(direct_cases) == 3

    assert all(
        case.expected.max_graph_tool_calls
        == 1
        for case in graph_cases
    )

    assert all(
        case.expected.max_graph_tool_calls
        == 0
        for case in direct_cases
    )


def test_rejects_duplicate_case_ids(
    tmp_path: Path,
):
    path = tmp_path / "benchmark.yaml"

    path.write_text(
        """
version: 1
cases:
  - id: AGT-001
    category: conversational
    question: "Hello"
    expected:
      graphToolRequired: false
      maxGraphToolCalls: 0
      requiredAnswerValues: []

  - id: AGT-001
    category: conceptual
    question: "What is a graph?"
    expected:
      graphToolRequired: false
      maxGraphToolCalls: 0
      requiredAnswerValues: []
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="Duplicate",
    ):
        load_agent_benchmark(path)


def test_rejects_unsupported_category(
    tmp_path: Path,
):
    path = tmp_path / "benchmark.yaml"

    path.write_text(
        """
version: 1
cases:
  - id: AGT-001
    category: unknown_category
    question: "Hello"
    expected:
      graphToolRequired: false
      maxGraphToolCalls: 0
      requiredAnswerValues: []
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="unsupported category",
    ):
        load_agent_benchmark(path)


def test_rejects_tool_call_for_direct_case(
    tmp_path: Path,
):
    path = tmp_path / "benchmark.yaml"

    path.write_text(
        """
version: 1
cases:
  - id: AGT-001
    category: conversational
    question: "Hello"
    expected:
      graphToolRequired: false
      maxGraphToolCalls: 1
      requiredAnswerValues: []
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="requires maxGraphToolCalls=0",
    ):
        load_agent_benchmark(path)


def test_rejects_required_tool_with_zero_calls(
    tmp_path: Path,
):
    path = tmp_path / "benchmark.yaml"

    path.write_text(
        """
version: 1
cases:
  - id: AGT-001
    category: filtering
    question: "Find executions"
    expected:
      graphToolRequired: true
      maxGraphToolCalls: 0
      requiredAnswerValues: []
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="requires maxGraphToolCalls >= 1",
    ):
        load_agent_benchmark(path)