MATCH traceabilityPath =
    (feature:Feature)
    -[:HAS_REQUIREMENT]->(requirement:Requirement)
    <-[:VERIFIES]-(test:Test)
    <-[:EXECUTION_OF]-(execution:TestExecution)
    -[:HAS_DEFECT_TICKET]->(ticket:DefectTicket)

RETURN traceabilityPath;