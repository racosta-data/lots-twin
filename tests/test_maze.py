import pytest

from lots_twin.domain.enums import State, Subreason
from lots_twin.domain.errors import ContractError
from lots_twin.domain.models import Context
from lots_twin.pipeline.cases import CLEAN
from lots_twin.pipeline.catalog import load_catalog
from tests.conftest import ROOT


def ctx(**kw):
    return Context(**{**CLEAN, **kw})


def test_stops_at_first_wall_and_never_reads_later_cells(catalog):
    out = catalog.maze.evaluate(ctx(scene_in_registry=True, usable_coverage_pct=None))
    assert out[0].result.state is State.FAIL
    assert all(o.result.subreason is Subreason.NOT_EVALUATED for o in out[1:])


def test_always_nine_outcomes(catalog):
    assert len(catalog.maze.evaluate(ctx())) == 9


def test_absent_is_unknown_present_but_wrong_is_fail(catalog):
    absent = catalog.maze.evaluate(ctx(baseline=None))[2].result
    wrong = catalog.maze.evaluate(ctx(baseline="02.14"))[2].result
    assert absent.state is State.UNKNOWN and absent.subreason is Subreason.MISSING_INPUT
    assert wrong.state is State.FAIL


def test_unseen_baseline_fails_until_added_on_purpose(catalog):
    assert catalog.maze.evaluate(ctx(baseline="06.00"))[2].result.state is State.FAIL


def test_real_catalog_refuses_to_run_with_pending_c3():
    with pytest.raises(ContractError):
        load_catalog(ROOT / "config/rules/v1.yaml")
