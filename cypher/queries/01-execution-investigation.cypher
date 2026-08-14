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