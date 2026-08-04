# Data Model

## Feature

Represents a user-visible automotive capability.

### Properties

* `id` — unique identifier
* `name` — feature name
* `description` — short explanation of the feature

## Requirement

Represents an expected system behavior.

### Properties

* `id` — unique identifier
* `title` — short requirement name
* `description` — complete expected behavior
* `priority` — requirement importance
* `status` — current requirement status

## SoftwareComponent

Represents a software unit responsible for system behavior.

### Properties

* `id` — unique identifier
* `name` — component name
* `description` — component responsibility
* `version` — software version used in testing

## Test

Represents a reusable test definition.

### Properties

* `id` — unique identifier
* `title` — short test name
* `description` — behavior checked by the test
* `preconditions` — conditions required before execution
* `expectedResult` — expected outcome

## TestExecution

Represents one specific execution of a test.

### Properties

* `id` — unique identifier
* `executionDate` — date and time of execution
* `environment` — `SiL`, `HiL`, or `Vehicle`
* `result` — `Passed` or `Failed`
* `reconnectionTimeSeconds` — measured reconnection time
* `softwareVersion` — software version tested

## TestTrace

Represents diagnostic information produced during a test execution.

### Properties

* `id` — unique identifier
* `timestamp` — time when the trace event occurred
* `level` — message level, such as `Info`, `Warning`, or `Error`
* `message` — diagnostic message

## DefectTicket

Represents a recorded software problem.

### Properties

* `id` — unique identifier
* `title` — short defect summary
* `description` — detailed problem description
* `status` — current ticket status
* `severity` — impact of the defect
* `createdDate` — date when the ticket was created
