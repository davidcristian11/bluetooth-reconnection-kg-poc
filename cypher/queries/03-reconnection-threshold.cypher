MATCH (execution:TestExecution)
      -[:EXECUTION_OF]->(test:Test)
      -[:VERIFIES]->(requirement:Requirement {id: 'REQ-002'})

WHERE execution.reconnectionTimeSeconds > 10.0

RETURN execution.id AS executionId,
       execution.environment AS environment,
       execution.result AS result,
       execution.reconnectionTimeSeconds AS reconnectionTimeSeconds,
       test.id AS testId,
       test.title AS testTitle,
       requirement.id AS requirementId

ORDER BY execution.reconnectionTimeSeconds DESC;