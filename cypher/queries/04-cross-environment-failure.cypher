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
       size(environments) AS environmentCount

ORDER BY environmentCount DESC;