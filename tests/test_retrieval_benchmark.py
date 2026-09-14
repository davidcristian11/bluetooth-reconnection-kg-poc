from pathlib import Path

import pytest

from retrieval_benchmark import (
    RetrievalBenchmarkDefinitionError,
    load_retrieval_benchmark,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def write_benchmark(tmp_path, content: str) -> Path:
    path = tmp_path / "retrieval_benchmark.yaml"
    path.write_text(content, encoding="utf-8")
    return path


def test_project_retrieval_benchmark_loads():
    path = PROJECT_ROOT / "evaluation" / "retrieval_benchmark.yaml"

    version, cases = load_retrieval_benchmark(path)

    assert version == 1
    assert len(cases) == 10
    assert cases[0].id == "RET-001"
    assert cases[-1].id == "RET-010"
    assert cases[0].top_k == 10
    assert cases[4].top_k == 15
    assert cases[6].top_k == 20


def test_case_uses_default_top_k(tmp_path):
    path = write_benchmark(
        tmp_path,
        """
version: 1
defaultTopK: 8
cases:
  - id: RET-001
    category: direct_relationship
    question: What requirement does TEST-006 verify?
    expected:
      result: non_empty
""",
    )

    _, cases = load_retrieval_benchmark(path)

    assert cases[0].top_k == 8


def test_case_can_override_top_k(tmp_path):
    path = write_benchmark(
        tmp_path,
        """
version: 1
defaultTopK: 8
cases:
  - id: RET-001
    category: direct_relationship
    question: What requirement does TEST-006 verify?
    topK: 20
    expected:
      result: non_empty
""",
    )

    _, cases = load_retrieval_benchmark(path)

    assert cases[0].top_k == 20


def test_duplicate_case_ids_are_rejected(tmp_path):
    path = write_benchmark(
        tmp_path,
        """
version: 1
defaultTopK: 10
cases:
  - id: RET-001
    category: direct_relationship
    question: First question
    expected:
      result: non_empty
  - id: RET-001
    category: direct_relationship
    question: Second question
    expected:
      result: non_empty
""",
    )

    with pytest.raises(
        RetrievalBenchmarkDefinitionError,
        match="Duplicate retrieval benchmark case id",
    ):
        load_retrieval_benchmark(path)


def test_unsupported_category_is_rejected(tmp_path):
    path = write_benchmark(
        tmp_path,
        """
version: 1
defaultTopK: 10
cases:
  - id: RET-001
    category: unknown_category
    question: Example question
    expected:
      result: non_empty
""",
    )

    with pytest.raises(
        RetrievalBenchmarkDefinitionError,
        match="Unsupported retrieval category",
    ):
        load_retrieval_benchmark(path)


def test_invalid_top_k_is_rejected(tmp_path):
    path = write_benchmark(
        tmp_path,
        """
version: 1
defaultTopK: 10
cases:
  - id: RET-001
    category: direct_relationship
    question: Example question
    topK: 0
    expected:
      result: non_empty
""",
    )

    with pytest.raises(
        RetrievalBenchmarkDefinitionError,
        match="topK for RET-001 must be a positive integer",
    ):
        load_retrieval_benchmark(path)