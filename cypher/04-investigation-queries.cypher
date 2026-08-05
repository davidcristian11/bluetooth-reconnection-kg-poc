// investigate the main graph path for test execution EXEC-010

MATCH mainPath =
    (execution:TestExecution {id: 'EXEC-010'})
    -[:EXECUTION_OF]->(test:Test)
    -[:VERIFIES]->(requirement:Requirement)

OPTIONAL MATCH tracePath =
    (execution)-[:PRODUCES]->(trace:TestTrace)

OPTIONAL MATCH ticketPath =
    (execution)-[:HAS_DEFECT_TICKET]->(ticket:DefectTicket)

OPTIONAL MATCH componentPath =
    (ticket)-[:AFFECTS]->(component:SoftwareComponent)

RETURN mainPath,
       tracePath,
       ticketPath,
       componentPath;