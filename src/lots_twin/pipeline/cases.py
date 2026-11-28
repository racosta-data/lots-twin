from dataclasses import dataclass
from pathlib import Path

import yaml

from ..domain.models import Context, VectorFacts

CLEAN = dict(scene_in_registry=False, hash_published="abc", hash_received="abc", file_opens=True, baseline="05.11",
             crs_metadata=32618, crs_file=32618, footprint_valid=True, bbox_matches_raster=True, covered_pct=100.0,
             bands=["B02", "B03", "B04", "B08", "SCL"], metadata_offset=-1000, max_dn=12000, usable_coverage_pct=96.0)


@dataclass
class Case:
    id: str
    description: str
    ctx: Context
    vector: VectorFacts
    cells: list
    zone: str
    code: str | None


def load_case(path: str | Path) -> Case:
    d = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    ctx = Context(**{**CLEAN, **d.get("facts", {})})
    vector = VectorFacts(**d.get("vector", {}))
    exp = d["expected"]
    return Case(d["id"], d["description"], ctx, vector, exp["cells"], exp["zone"], exp.get("code"))


def load_cases(folder: str | Path) -> list:
    return [load_case(p) for p in sorted(Path(folder).glob("*.yaml"))]
