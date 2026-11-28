from pathlib import Path

import pytest

from lots_twin.pipeline.catalog import load_catalog

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def catalog():
    # C3 threshold is a simulation placeholder (80), not a calibrated value.
    return load_catalog(ROOT / "config/rules/v1.yaml", overrides={"C3": {"min_usable_coverage_pct": 80}}, allow_pending=True)
