# Synthetic Dataset

This directory contains the synthetic dataset used by the Bluetooth Reconnection Knowledge Graph PoC.

## Directory structure

* `nodes/` contains one CSV file for each ontology concept.
* `relationships/` contains one CSV file for each ontology relationship.

## ID conventions

| Concept           | ID format   |
| ----------------- | ----------- |
| Feature           | `FEAT-001`  |
| Requirement       | `REQ-001`   |
| SoftwareComponent | `COMP-001`  |
| Test              | `TEST-001`  |
| TestExecution     | `EXEC-001`  |
| TestTrace         | `TRACE-001` |
| DefectTicket      | `DEF-001`   |

IDs must be unique and must not change after they are assigned.

## File conventions

* CSV files use commas as separators.
* The first row contains column names.
* Text containing commas must be enclosed in double quotes.
* Dates use ISO format: `YYYY-MM-DD`.
* Timestamps use ISO format: `YYYY-MM-DDTHH:MM:SS`.
* Missing values are represented by an empty CSV field.
* File names use lowercase snake case.
* CSV property names match the ontology property names.

## Relationship conventions

Relationship CSV files contain the IDs of the connected nodes.

For example:

```csv
featureId,requirementId
FEAT-001,REQ-001
```

The relationship direction is determined by the file name and follows the ontology model.
