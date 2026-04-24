-- Platform API interview SQL drill
-- Recommended DB file:
-- data/results/automation_platform.db
--
-- Example local usage:
-- sqlite3 data/results/automation_platform.db
-- .read practice/sql/run-api-sql-drill.sql

-- 1. List all runs, newest first
SELECT run_id, testline, executor_type, status, created_at
FROM runs
ORDER BY created_at DESC;

-- 2. Query one run by run_id
SELECT *
FROM runs
WHERE run_id = 'run-20260423093000000';

-- 3. Query runs under one testline
SELECT run_id, testline, status, created_at
FROM runs
WHERE testline = 'T813'
ORDER BY created_at DESC;

-- 4. Count runs per testline
SELECT testline, COUNT(*) AS run_count
FROM runs
GROUP BY testline
ORDER BY run_count DESC;

-- 5. Count runs per status
SELECT status, COUNT(*) AS status_count
FROM runs
GROUP BY status
ORDER BY status_count DESC;

-- 6. Query runs that enabled KPI generator
SELECT run_id, testline, enable_kpi_generator, enable_kpi_anomaly_detector, created_at
FROM runs
WHERE enable_kpi_generator = 1
ORDER BY created_at DESC;

-- 7. Query runs that enabled both generator and detector
SELECT run_id, testline, enable_kpi_generator, enable_kpi_anomaly_detector
FROM runs
WHERE enable_kpi_generator = 1
  AND enable_kpi_anomaly_detector = 1;

-- 8. Query completed runs that already have Jenkins callback info
SELECT run_id, status, jenkins_build_ref, started_at, finished_at
FROM runs
WHERE status = 'completed'
  AND jenkins_build_ref <> '';

-- 9. Query suspicious rows with empty message
SELECT run_id, status, message, updated_at
FROM runs
WHERE message = '';

-- 10. Query runs created after a timestamp
SELECT run_id, testline, created_at
FROM runs
WHERE created_at >= '2026-04-23T09:00:00+08:00'
ORDER BY created_at DESC;

-- 11. Query runs whose workflow name contains a keyword
SELECT run_id, workflow_name, executor_type, created_at
FROM runs
WHERE workflow_name LIKE '%Attach%'
ORDER BY created_at DESC;

-- 12. Query runs whose detector summary is not empty
SELECT run_id, status, detector_summary_json, updated_at
FROM runs
WHERE detector_summary_json <> '{}';
