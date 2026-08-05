// Feature HAS_REQUIREMENT Requirement
LOAD CSV WITH HEADERS
FROM 'file:///relationships/feature_has_requirement.csv' AS row
MATCH (feature:Feature {id: row.featureId})
MATCH (requirement:Requirement {id: row.requirementId})
MERGE (feature)-[:HAS_REQUIREMENT]->(requirement);


// SoftwareComponent IMPLEMENTS Requirement
LOAD CSV WITH HEADERS
FROM 'file:///relationships/software_component_implements_requirement.csv' AS row
MATCH (component:SoftwareComponent {id: row.componentId})
MATCH (requirement:Requirement {id: row.requirementId})
MERGE (component)-[:IMPLEMENTS]->(requirement);


// Test VERIFIES Requirement
LOAD CSV WITH HEADERS
FROM 'file:///relationships/test_verifies_requirement.csv' AS row
MATCH (test:Test {id: row.testId})
MATCH (requirement:Requirement {id: row.requirementId})
MERGE (test)-[:VERIFIES]->(requirement);


// TestExecution EXECUTION_OF Test
LOAD CSV WITH HEADERS
FROM 'file:///relationships/test_execution_execution_of_test.csv' AS row
MATCH (execution:TestExecution {id: row.executionId})
MATCH (test:Test {id: row.testId})
MERGE (execution)-[:EXECUTION_OF]->(test);


// TestExecution PRODUCES TestTrace
LOAD CSV WITH HEADERS
FROM 'file:///relationships/test_execution_produces_trace.csv' AS row
MATCH (execution:TestExecution {id: row.executionId})
MATCH (trace:TestTrace {id: row.traceId})
MERGE (execution)-[:PRODUCES]->(trace);


// TestExecution HAS_DEFECT_TICKET DefectTicket
LOAD CSV WITH HEADERS
FROM 'file:///relationships/test_execution_has_defect_ticket.csv' AS row
MATCH (execution:TestExecution {id: row.executionId})
MATCH (ticket:DefectTicket {id: row.defectTicketId})
MERGE (execution)-[:HAS_DEFECT_TICKET]->(ticket);


// DefectTicket AFFECTS SoftwareComponent
LOAD CSV WITH HEADERS
FROM 'file:///relationships/defect_ticket_affects_component.csv' AS row
MATCH (ticket:DefectTicket {id: row.defectTicketId})
MATCH (component:SoftwareComponent {id: row.componentId})
MERGE (ticket)-[:AFFECTS]->(component);