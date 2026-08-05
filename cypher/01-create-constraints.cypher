CREATE CONSTRAINT feature_id_unique IF NOT EXISTS
FOR (n:Feature)
REQUIRE n.id IS UNIQUE;

CREATE CONSTRAINT requirement_id_unique IF NOT EXISTS
FOR (n:Requirement)
REQUIRE n.id IS UNIQUE;

CREATE CONSTRAINT software_component_id_unique IF NOT EXISTS
FOR (n:SoftwareComponent)
REQUIRE n.id IS UNIQUE;

CREATE CONSTRAINT test_id_unique IF NOT EXISTS
FOR (n:Test)
REQUIRE n.id IS UNIQUE;

CREATE CONSTRAINT test_execution_id_unique IF NOT EXISTS
FOR (n:TestExecution)
REQUIRE n.id IS UNIQUE;

CREATE CONSTRAINT test_trace_id_unique IF NOT EXISTS
FOR (n:TestTrace)
REQUIRE n.id IS UNIQUE;

CREATE CONSTRAINT defect_ticket_id_unique IF NOT EXISTS
FOR (n:DefectTicket)
REQUIRE n.id IS UNIQUE;