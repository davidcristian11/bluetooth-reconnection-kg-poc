MATCH (execution:TestExecution)

RETURN execution.environment AS environment,
       sum(
           CASE
               WHEN execution.result = 'PASS' THEN 1
               ELSE 0
           END
       ) AS passCount,
       sum(
           CASE
               WHEN execution.result = 'FAIL' THEN 1
               ELSE 0
           END
       ) AS failCount,
       count(execution) AS totalExecutions

ORDER BY environment;