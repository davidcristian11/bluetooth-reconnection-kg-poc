GRAPH_SCHEMA = """
Use only the graph schema below.
Do not assume that other node labels, relationships, or properties exist.

Node labels and properties:

Feature
- id
- name
- description
- sourceSystem

Requirement
- id
- title
- description
- priority
- status
- sourceSystem

SoftwareComponent
- id
- name
- description
- version
- sourceSystem

Test
- id
- title
- description
- preconditions
- expectedResult
- sourceSystem

TestExecution
- id
- executionDate
- environment
- result
- reconnectionTimeSeconds
- softwareVersion
- sourceSystem

TestTrace
- id
- timestamp
- level
- message
- sourceSystem

DefectTicket
- id
- title
- description
- status
- severity
- createdDate
- sourceSystem


Relationships:

(Feature)-[:HAS_REQUIREMENT]->(Requirement)

(SoftwareComponent)-[:IMPLEMENTS]->(Requirement)

(Test)-[:VERIFIES]->(Requirement)

(TestExecution)-[:EXECUTION_OF]->(Test)

(TestExecution)-[:PRODUCES]->(TestTrace)

(TestExecution)-[:HAS_DEFECT_TICKET]->(DefectTicket)

(DefectTicket)-[:AFFECTS]->(SoftwareComponent)


Known property values:

Feature.sourceSystem:
- ProductDefinitionSystem

Requirement.sourceSystem:
- RequirementsSystem

SoftwareComponent.sourceSystem:
- SoftwareArchitectureSystem

Test.sourceSystem:
- TestManagementSystem

TestExecution.environment:
- SiL
- HiL
- Vehicle

TestExecution.result:
- PASS
- FAIL

TestExecution.sourceSystem:
- TestManagementSystem

TestTrace.sourceSystem:
- TraceRepository

DefectTicket.sourceSystem:
- DefectTrackingSystem

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