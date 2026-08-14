MATCH (requirement:Requirement)

WHERE NOT EXISTS {
    MATCH (:Test)-[:VERIFIES]->(requirement)
}

RETURN requirement.id AS requirementId,
       requirement.title AS requirementTitle,
       requirement.priority AS priority,
       requirement.status AS status

ORDER BY requirement.id;