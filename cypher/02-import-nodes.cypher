// Import Feature nodes
LOAD CSV WITH HEADERS FROM 'file:///nodes/features.csv' AS row // mounted directory from docker-compose.yml
MERGE (n:Feature {id: row.id}) // merge == create a node if not exists, otherwise match existing node
SET n.name = row.name,
    n.description = row.description;

// Import Requirement nodes
LOAD CSV WITH HEADERS FROM 'file:///nodes/requirements.csv' AS row
MERGE (n:Requirement {id: row.id})
SET n.title = row.title,
    n.description = row.description,
    n.priority = row.priority,
    n.status = row.status;

LOAD CSV WITH HEADERS FROM 'file:///nodes/software_components.csv' AS row
MERGE (n:SoftwareComponent {id: row.id})
SET n.name = row.name,
    n.description = row.description,
    n.version = row.version;

LOAD CSV WITH HEADERS FROM 'file:///nodes/tests.csv' AS row
MERGE (n:Test {id: row.id})
SET n.title = row.title,
    n.description = row.description,
    n.preconditions = row.preconditions,
    n.expectedResult = row.expectedResult;

LOAD CSV WITH HEADERS FROM 'file:///nodes/test_executions.csv' AS row
MERGE (n:TestExecution {id: row.id})
SET n.executionDate =
        CASE
            WHEN row.executionDate IS NULL OR trim(row.executionDate) = ''
            THEN null
            ELSE date(row.executionDate)
        END,
    n.environment = row.environment,
    n.result = row.result,
    n.reconnectionTimeSeconds =
        CASE
            WHEN row.reconnectionTimeSeconds IS NULL
                 OR trim(row.reconnectionTimeSeconds) = ''
            THEN null
            ELSE toFloat(row.reconnectionTimeSeconds)
        END,
    n.softwareVersion = row.softwareVersion;

LOAD CSV WITH HEADERS FROM 'file:///nodes/test_traces.csv' AS row
MERGE (n:TestTrace {id: row.id})
SET n.timestamp =
        CASE
            WHEN row.timestamp IS NULL OR trim(row.timestamp) = ''
            THEN null
            ELSE datetime(row.timestamp)
        END,
    n.level = row.level,
    n.message = row.message;

LOAD CSV WITH HEADERS FROM 'file:///nodes/defect_tickets.csv' AS row
MERGE (n:DefectTicket {id: row.id})
SET n.title = row.title,
    n.description = row.description,
    n.status = row.status,
    n.severity = row.severity,
    n.createdDate =
        CASE
            WHEN row.createdDate IS NULL OR trim(row.createdDate) = ''
            THEN null
            ELSE date(row.createdDate)
        END;