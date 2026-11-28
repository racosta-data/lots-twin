import pytest

from lots_twin.domain.errors import ContractError
from lots_twin.domain.models import Context, VectorFacts
from lots_twin.pipeline.cases import CLEAN
from lots_twin.pipeline.conservation import check_conservation
from lots_twin.pipeline.determinism import stable_hash
from lots_twin.pipeline.learning import suggest_threshold
from lots_twin.pipeline.runner import evaluate_scene, run_batch
from lots_twin.pipeline.storage import write_evaluations
from lots_twin.pipeline.views import cell_memory, drift_alerts


def scene(i, **kw):
    return (f"S{i}", "08001", Context(**{**CLEAN, **kw}), VectorFacts())


def test_conservation_passes_and_breaks(catalog):
    rows, zones = run_batch([scene(1), scene(2, scene_in_registry=True)], catalog, "r1", "t")
    assert len(rows) == 18 and sorted(zones.values()) == ["rejected", "validated"]
    with pytest.raises(ContractError, match="DQ-560"):
        check_conservation(3, {"validated": 1, "rejected": 1})


def test_hash_is_deterministic_and_ignores_run_and_time(catalog):
    a, _, _ = evaluate_scene("S1", "08001", Context(**CLEAN), VectorFacts(), catalog, "run-A", "t")
    b, _, _ = evaluate_scene("S1", "08001", Context(**CLEAN), VectorFacts(), catalog, "run-B", "t")
    assert a[0]["evaluated_at"] != b[0]["evaluated_at"] or a[0]["run_id"] != b[0]["run_id"]
    assert stable_hash(a) == stable_hash(b)
    b[3]["state"] = "FAIL"
    assert stable_hash(a) != stable_hash(b)


def test_evaluation_file_is_write_once(tmp_path, catalog):
    rows, _ = run_batch([scene(1)], catalog, "r1", "t")
    write_evaluations(rows, tmp_path / "r1.parquet")
    with pytest.raises(FileExistsError):
        write_evaluations(rows, tmp_path / "r1.parquet")


def test_cell_memory_and_drift_alert(tmp_path, catalog):
    # 6 scenes, 4 of them with an unseen baseline: A3 fails for 4 of 6 evaluated (67% > 50%)
    scenes = [scene(i, baseline="06.00" if i < 4 else "05.11") for i in range(6)]
    rows, _ = run_batch(scenes, catalog, "run-1", "t")
    write_evaluations(rows, tmp_path / "run-1.parquet")
    glob = str(tmp_path / "*.parquet")
    memory = {(c, t): (p, f, u) for c, t, p, f, u, *_ in cell_memory(glob)}
    assert memory[("A3", "08001")] == (2, 4, 0)
    alerts = drift_alerts(glob, min_scenes=5, max_fail_rate=0.5)
    assert [(a[0], a[1]) for a in alerts] == [("run-1", "A3")]


def test_no_alert_when_failures_are_rare(tmp_path, catalog):
    scenes = [scene(i, baseline="06.00" if i == 0 else "05.11") for i in range(8)]
    rows, _ = run_batch(scenes, catalog, "run-1", "t")
    write_evaluations(rows, tmp_path / "run-1.parquet")
    assert drift_alerts(str(tmp_path / "*.parquet")) == []


def test_threshold_suggestion_finds_the_valley_and_is_only_a_proposal():
    clear, cloudy = [95, 96, 97, 98, 94, 99, 93, 96], [5, 10, 12, 8, 15, 11, 9, 14]
    s = suggest_threshold(clear + cloudy + [55])
    assert s["method"] == "valley" and 15 <= s["suggested"] <= 90 and "needs approval" in s["note"]
    assert suggest_threshold([50, 60])["suggested"] is None
