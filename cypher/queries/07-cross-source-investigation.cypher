MATCH (execution:TestExecution {id: 'EXEC-010'})
      -[:EXECUTION_OF]->(test:Test)
      -[:VERIFIES]->(requirement:Requirement)
      <-[:HAS_REQUIREMENT]-(feature:Feature)

OPTIONAL MATCH
    (implementingComponent:SoftwareComponent)-[:IMPLEMENTS]->(requirement)

OPTIONAL MATCH
    (execution)-[:PRODUCES]->(trace:TestTrace)

OPTIONAL MATCH
    (execution)-[:HAS_DEFECT_TICKET]->(ticket:DefectTicket)
    -[:AFFECTS]->(affectedComponent:SoftwareComponent)

RETURN execution.id AS executionId,
       execution.sourceSystem AS executionSourceSystem,
       execution.environment AS environment,
       execution.result AS result,
       execution.reconnectionTimeSeconds AS reconnectionTimeSeconds,
       test.id AS testId,
       test.sourceSystem AS testSourceSystem,
       requirement.id AS requirementId,
       requirement.sourceSystem AS requirementSourceSystem,
       feature.id AS featureId,
       feature.sourceSystem AS featureSourceSystem,
       implementingComponent.id AS implementingComponentId,
       implementingComponent.sourceSystem AS implementingComponentSourceSystem,
       collect(
           DISTINCT {
               id: trace.id,
               sourceSystem: trace.sourceSystem,
               level: trace.level,
               message: trace.message
           }
       ) AS traces,
       ticket.id AS defectTicketId,
       ticket.sourceSystem AS defectSourceSystem,
       affectedComponent.id AS affectedComponentId,
       affectedComponent.sourceSystem AS affectedComponentSourceSystem;