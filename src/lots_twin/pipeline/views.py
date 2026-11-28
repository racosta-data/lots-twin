import duckdb

CELL_MEMORY_SQL = """
SELECT cell, territory_code,
       count(*) FILTER (WHERE state = 'PASS')    AS pass_count,
       count(*) FILTER (WHERE state = 'FAIL')    AS fail_count,
       count(*) FILTER (WHERE state = 'UNKNOWN' AND subreason <> 'NOT_EVALUATED') AS unknown_count,
       min(evaluated_at) AS first_seen,
       max(evaluated_at) AS last_seen,
       max(evaluated_at) FILTER (WHERE state <> 'PASS' AND subreason IS DISTINCT FROM 'NOT_EVALUATED') AS last_non_pass
FROM read_parquet('{glob}')
GROUP BY cell, territory_code
ORDER BY territory_code, cell
"""

DRIFT_SQL = """
SELECT run_id, cell,
       count(*) FILTER (WHERE state IN ('PASS','FAIL')) AS evaluated,
       count(*) FILTER (WHERE state = 'FAIL')           AS failed,
       round(count(*) FILTER (WHERE state = 'FAIL')::DOUBLE
             / nullif(count(*) FILTER (WHERE state IN ('PASS','FAIL')), 0), 3) AS fail_rate
FROM read_parquet('{glob}')
GROUP BY run_id, cell
HAVING count(*) FILTER (WHERE state IN ('PASS','FAIL')) >= {min_scenes}
   AND count(*) FILTER (WHERE state = 'FAIL')::DOUBLE
       / count(*) FILTER (WHERE state IN ('PASS','FAIL')) > {max_fail_rate}
ORDER BY run_id, cell
"""


def cell_memory(glob: str) -> list:
    """The persistent switch of the maze: per cell and territory, what has been seen so far."""
    return duckdb.sql(CELL_MEMORY_SQL.format(glob=glob)).fetchall()


def drift_alerts(glob: str, min_scenes: int = 5, max_fail_rate: float = 0.5) -> list:
    """Cells failing for more than max_fail_rate of the evaluated scenes in one run.
    Usually the source changed (for example a new baseline), not the atmosphere."""
    return duckdb.sql(DRIFT_SQL.format(glob=glob, min_scenes=min_scenes, max_fail_rate=max_fail_rate)).fetchall()
