from pathlib import Path

import pytest

from flat_retriever import (
    FlatRetrievalError,
    LexicalFlatRetriever,
    load_flat_documents,
    tokenize,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def build_retriever():
    return LexicalFlatRetriever.from_project_data(
        PROJECT_ROOT
    )


def test_flat_corpus_contains_all_source_rows():
    documents = load_flat_documents(PROJECT_ROOT)

    node_documents = [
        document
        for document in documents
        if document.kind == "node"
    ]

    relationship_documents = [
        document
        for document in documents
        if document.kind == "relationship"
    ]

    assert len(documents) == 116
    assert len(node_documents) == 52
    assert len(relationship_documents) == 64


def test_node_document_contains_source_system_metadata():
    documents = load_flat_documents(PROJECT_ROOT)

    document = next(
        item
        for item in documents
        if item.document_id
        == "node:TestExecution:EXEC-010"
    )

    assert "EXEC-010" in document.text
    assert "Vehicle" in document.text
    assert "FAIL" in document.text
    assert "18.0" in document.text
    assert "TestManagementSystem" in document.text


def test_relationship_document_contains_only_direct_fact():
    documents = load_flat_documents(PROJECT_ROOT)

    document = next(
        item
        for item in documents
        if item.document_id
        == "relationship:VERIFIES:TEST-006:REQ-006"
    )

    assert document.text == (
        "Test TEST-006 VERIFIES Requirement REQ-006"
    )
    assert document.metadata["sourceId"] == "TEST-006"
    assert document.metadata["targetId"] == "REQ-006"


def test_tokenizer_normalizes_common_inflections():
    assert "affect" in tokenize("affected AFFECTS")
    assert "verify" in tokenize("verifying VERIFIES")
    assert "produc" in tokenize("produced PRODUCES")


def test_direct_relationship_is_ranked_first():
    retriever = build_retriever()

    results = retriever.search(
        "What requirement does TEST-006 verify?",
        top_k=10,
    )

    assert results[0].document.document_id == (
        "relationship:VERIFIES:TEST-006:REQ-006"
    )


def test_one_to_many_relationships_are_ranked_first():
    retriever = build_retriever()

    results = retriever.search(
        "Which traces were produced by EXEC-006?",
        top_k=3,
    )

    assert {
        result.document.metadata["targetId"]
        for result in results
    } == {
        "TRACE-003",
        "TRACE-004",
        "TRACE-005",
    }


def test_flat_retrieval_does_not_traverse_relationships():
    retriever = build_retriever()

    results = retriever.search(
        "What happened during EXEC-010?",
        top_k=15,
    )

    document_ids = {
        result.document.document_id
        for result in results
    }

    assert (
        "relationship:HAS_DEFECT_TICKET:EXEC-010:DEF-001"
        in document_ids
    )
    assert (
        "relationship:AFFECTS:DEF-001:COMP-002"
        not in document_ids
    )


def test_search_is_deterministic():
    retriever = build_retriever()

    first = retriever.search(
        "Which tests verify REQ-004?",
        top_k=10,
    )
    second = retriever.search(
        "Which tests verify REQ-004?",
        top_k=10,
    )

    assert first == second


def test_invalid_top_k_is_rejected():
    retriever = build_retriever()

    with pytest.raises(
        FlatRetrievalError,
        match="top_k must be a positive integer",
    ):
        retriever.search(
            "Example question",
            top_k=0,
        )