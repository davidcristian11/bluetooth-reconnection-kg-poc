GRAPH_SCHEMA = """
Use only the graph schema below.
Do not assume that other node labels, relationships, or properties exist.

Node labels and properties:

Feature
- id
- name
- description

Requirement
- id
- title
- description
- priority
- status

SoftwareComponent
- id
- name
- description
- version

Test
- id
- title
- description
- preconditions
- expectedResult

TestExecution
- id
- executionDate
- environment
- result
- reconnectionTimeSeconds
- softwareVersion

TestTrace
- id
- timestamp
- level
- message

DefectTicket
- id
- title
- description
- status
- severity
- createdDate


Relationships:

(Feature)-[:HAS_REQUIREMENT]->(Requirement)

(SoftwareComponent)-[:IMPLEMENTS]->(Requirement)

(Test)-[:VERIFIES]->(Requirement)

(TestExecution)-[:EXECUTION_OF]->(Test)

(TestExecution)-[:PRODUCES]->(TestTrace)

(TestExecution)-[:HAS_DEFECT_TICKET]->(DefectTicket)

(DefectTicket)-[:AFFECTS]->(SoftwareComponent)


Known property values:

TestExecution.environment:
- SiL
- HiL
- Vehicle

TestExecution.result:
- PASS
- FAIL

Known ID formats:

Feature:
- FEAT-*

Requirement:
- REQ-*

SoftwareComponent:
- COMP-*

Test:
- TEST-*

TestExecution:
- EXEC-*

TestTrace:
- TRACE-*

DefectTicket:
- DEF-*
"""