from collections import Counter
from datetime import datetime, timezone
from typing import Optional

from ..domain.models import Context, VectorFacts
from ..domain.routing import route_zone
from ..domain.vector_track import evaluate_vector_track
from .catalog import RuleCatalog
from .conservation import check_conservation


def evaluate_scene(scene_id: str, territory_code: str, ctx: Context, vector: VectorFacts, catalog: RuleCatalog,
                   run_id: str, code_version: str, now: Optional[datetime] = None) -> tuple:
    """Run one scene. Returns (evaluation rows, zone, code). Always 9 rows."""
    now = now or datetime.now(timezone.utc)
    outcomes = catalog.maze.evaluate(ctx, evaluate_vector_track(vector))
    zone, code = route_zone(outcomes)
    rows = [{
        "run_id": run_id, "scene_id": scene_id, "territory_code": territory_code, "cell": o.cell,
        "state": o.result.state.value, "subreason": o.result.subreason.value if o.result.subreason else None,
        "measured_value": o.result.measured, "threshold_applied": str(sorted(o.threshold.items())),
        "rule_version": o.rule_version, "dq_code": o.result.code.value if o.result.code else None,
        "code_version": code_version, "evaluated_at": now.isoformat(),
    } for o in outcomes]
    return rows, zone, code


def run_batch(scenes: list, catalog: RuleCatalog, run_id: str, code_version: str) -> tuple:
    """scenes: list of (scene_id, territory_code, Context, VectorFacts). Returns (rows, zones per scene)."""
    rows, zones = [], {}
    for scene_id, territory, ctx, vector in scenes:
        r, zone, _ = evaluate_scene(scene_id, territory, ctx, vector, catalog, run_id, code_version)
        rows.extend(r)
        zones[scene_id] = zone.value
    check_conservation(len(scenes), Counter(zones.values()))
    assert len(rows) == 9 * len(scenes)
    return rows, zones
