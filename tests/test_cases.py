from pathlib import Path

import pytest

from lots_twin.pipeline.cases import load_cases
from lots_twin.pipeline.runner import evaluate_scene

CASES = load_cases(Path(__file__).parent / "fixtures" / "cases")


def test_there_are_20_cases():
    assert len(CASES) == 20


@pytest.mark.parametrize("case", CASES, ids=[c.id for c in CASES])
def test_case(case, catalog):
    rows, zone, code = evaluate_scene(case.id, "08001", case.ctx, case.vector, catalog, "run-test", "test")
    assert len(rows) == 9
    assert [r["state"] for r in rows] == case.cells
    assert zone.value == case.zone
    assert (code.value if code else None) == case.code
