# Data Model

## Feature

Represents a user-visible automotive capability.

### Properties

* `id` — unique identifier
* `name` — feature name
* `description` — short explanation of the feature
* `sourceSystem` — synthetic source system from which the feature record originates

## Requirement

Represents an expected system behavior.

### Properties

* `id` — unique identifier
* `title` — short requirement name
* `description` — complete expected behavior
* `priority` — requirement importance
* `status` — current requirement status
* `sourceSystem` — synthetic source system from which the requirement record originates

## SoftwareComponent

Represents a software unit responsible for system behavior.

### Properties

* `id` — unique identifier
* `name` — component name
* `description` — component responsibility
* `version` — software version used in testing
* `sourceSystem` — synthetic source system from which the component record originates

## Test

Represents a reusable test definition.

### Properties

* `id` — unique identifier
* `title` — short test name
* `description` — behavior checked by the test
* `preconditions` — conditions required before execution
* `expectedResult` — expected outcome
* `sourceSystem` — synthetic source system from which the test record originates

## TestExecution

Represents one specific execution of a test.

### Properties

* `id` — unique identifier
* `executionDate` — date of execution
* `environment` — `SiL`, `HiL`, or `Vehicle`
* `result` — `PASS` or `FAIL`
* `reconnectionTimeSeconds` — measured reconnection time
* `softwareVersion` — software version tested
* `sourceSystem` — synthetic source system from which the execution record originates

## TestTrace

Represents diagnostic information produced during a test execution.

### Properties

* `id` — unique identifier
* `timestamp` — time when the trace event occurred
* `level` — message level, such as `INFO`, `WARN`, or `ERROR`
* `message` — diagnostic message
* `sourceSystem` — synthetic source system from which the trace record originates

## DefectTicket

Represents a recorded software problem.

### Properties

* `id` — unique identifier
* `title` — short defect summary
* `description` — detailed problem description
* `status` — current ticket status
* `severity` — impact of the defect
* `createdDate` — date when the ticket was created
* `sourceSystem` — synthetic source system from which the defect record originates

---

## Synthetic Source-System Metadata

The `sourceSystem` property is lightweight provenance metadata. In this PoC, provenance means information about where an engineering record came from before it was represented in the common graph model.

The source-system names are intentionally generic and synthetic. They do not represent Porsche systems or claim any real enterprise ownership or architecture.

| Node label | `sourceSystem` |
| --- | --- |
| `Feature` | `ProductDefinitionSystem` |
| `Requirement` | `RequirementsSystem` |
| `SoftwareComponent` | `SoftwareArchitectureSystem` |
| `Test` | `TestManagementSystem` |
| `TestExecution` | `TestManagementSystem` |
| `TestTrace` | `TraceRepository` |
| `DefectTicket` | `DefectTrackingSystem` |

`sourceSystem` is modeled as a property rather than as a separate node because the current PoC only needs to record origin metadata. The graph does not yet model source systems as entities with their own relationships or lifecycle.

This keeps the model small while still allowing an investigation to demonstrate the main idea:

```text
multiple synthetic engineering source systems
→ common ontology
→ connected Knowledge Graph
→ cross-source investigation