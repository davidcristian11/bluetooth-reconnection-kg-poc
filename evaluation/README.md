# AI Evaluation Benchmark

## Purpose

This benchmark measures the current schema-guided Text-to-Cypher
pipeline against deterministic ground truth derived from the project's
synthetic Knowledge Graph dataset.

The benchmark evaluates three stages independently:

1. execution success;
2. graph retrieval correctness;
3. final answer correctness.

A case is fully correct only when all three checks pass.

## Benchmark dataset

The benchmark is defined in:

```text
evaluation/benchmark.yaml