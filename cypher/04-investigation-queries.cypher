// Query 1 - Complete investigation path for EXEC-010

MATCH mainPath =
    (execution:TestExecution {id: 'EXEC-010'})
    -[:EXECUTION_OF]->(test:Test)
    -[:VERIFIES]->(requirement:Requirement)
    <-[:HAS_REQUIREMENT]-(feature:Feature)

OPTIONAL MATCH implementationPath =
    (requirement)<-[:IMPLEMENTS]-(implementingComponent:SoftwareComponent)

OPTIONAL MATCH tracePath =
    (execution)-[:PRODUCES]->(trace:TestTrace)

OPTIONAL MATCH defectPath =
    (execution)-[:HAS_DEFECT_TICKET]->(ticket:DefectTicket)
    -[:AFFECTS]->(affectedComponent:SoftwareComponent)

RETURN mainPath,
       implementationPath,
       tracePath,
       defectPath;


// Query 2 - Investigation details for EXEC-010

MATCH (execution:TestExecution {id: 'EXEC-010'})
      -[:EXECUTION_OF]->(test:Test)
      -[:VERIFIES]->(requirement:Requirement)

OPTIONAL MATCH
    (component:SoftwareComponent)-[:IMPLEMENTS]->(requirement)

OPTIONAL MATCH
    (execution)-[:PRODUCES]->(trace:TestTrace)

OPTIONAL MATCH
    (execution)-[:HAS_DEFECT_TICKET]->(ticket:DefectTicket)

RETURN execution.id AS executionId,
       execution.environment AS environment,
       execution.result AS result,
       execution.reconnectionTimeSeconds AS reconnectionTimeSeconds,
       test.id AS testId,
       requirement.id AS requirementId,
       component.id AS componentId,
       component.name AS componentName,
       collect(DISTINCT trace.id) AS traces,
       collect(DISTINCT ticket.id) AS defectTickets;


// Query 3 - Requirements without test coverage

MATCH (requirement:Requirement)

WHERE NOT EXISTS {
    MATCH (:Test)-[:VERIFIES]->(requirement)
}

RETURN requirement.id AS requirementId,
       requirement.title AS requirementTitle,
       requirement.status AS status;


// Query 4 - Failed executions by environment

MATCH (execution:TestExecution)

WHERE execution.result = 'FAIL'

RETURN execution.id AS executionId,
       execution.environment AS environment,
       execution.executionDate AS executionDate,
       execution.reconnectionTimeSeconds AS reconnectionTimeSeconds,
       execution.softwareVersion AS softwareVersion

ORDER BY execution.environment,
         execution.id;


// Query 5 - Executions exceeding the 10-second threshold

MATCH (execution:TestExecution)
      -[:EXECUTION_OF]->(test:Test)

WHERE execution.reconnectionTimeSeconds > 10.0

RETURN execution.id AS executionId,
       execution.environment AS environment,
       execution.result AS result,
       execution.reconnectionTimeSeconds AS reconnectionTimeSeconds,
       test.id AS testId

ORDER BY execution.reconnectionTimeSeconds DESC;


// Query 6 - Same failure appearing in multiple environments

MATCH (execution:TestExecution)
      -[:HAS_DEFECT_TICKET]->(ticket:DefectTicket)

WHERE execution.result = 'FAIL'

WITH ticket,
     collect(DISTINCT execution.environment) AS environments,
     collect(DISTINCT execution.id) AS executions

WHERE size(environments) > 1

RETURN ticket.id AS defectTicketId,
       ticket.title AS defectTitle,
       environments,
       executions,
       size(environments) AS environmentCount;


// Query 7 - Components connected to failed executions

MATCH (execution:TestExecution)
      -[:EXECUTION_OF]->(test:Test)
      -[:VERIFIES]->(requirement:Requirement)
      <-[:IMPLEMENTS]-(component:SoftwareComponent)

WHERE execution.result = 'FAIL'

RETURN component.id AS componentId,
       component.name AS componentName,
       collect(DISTINCT execution.id) AS failedExecutions,
       count(DISTINCT execution) AS failureCount

ORDER BY failureCount DESC;


// Query 8 - Defect tickets and traces for failed executions

MATCH (execution:TestExecution)

WHERE execution.result = 'FAIL'

OPTIONAL MATCH
    (execution)-[:HAS_DEFECT_TICKET]->(ticket:DefectTicket)

OPTIONAL MATCH
    (execution)-[:PRODUCES]->(trace:TestTrace)

RETURN execution.id AS executionId,
       execution.environment AS environment,
       execution.reconnectionTimeSeconds AS reconnectionTimeSeconds,
       collect(DISTINCT ticket.id) AS defectTickets,
       collect(DISTINCT trace.id) AS traces,
       collect(DISTINCT trace.message) AS traceMessages

ORDER BY execution.id;


// Query 9 - Complete traceability from Feature to DefectTicket

MATCH traceabilityPath =
    (feature:Feature)
    -[:HAS_REQUIREMENT]->(requirement:Requirement)
    <-[:VERIFIES]-(test:Test)
    <-[:EXECUTION_OF]-(execution:TestExecution)
    -[:HAS_DEFECT_TICKET]->(ticket:DefectTicket)

RETURN traceabilityPath;


// Query 10 - Pass and fail counts by environment

MATCH (execution:TestExecution)

RETURN execution.environment AS environment,
       sum(
           CASE
               WHEN execution.result = 'PASS' THEN 1
               ELSE 0
           END
       ) AS passCount,
       sum(
           CASE
               WHEN execution.result = 'FAIL' THEN 1
               ELSE 0
           END
       ) AS failCount,
       count(execution) AS totalExecutions

ORDER BY environment;