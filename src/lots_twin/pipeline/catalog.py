from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import yaml

from ..domain.errors import ContractError
from ..domain.maze import CELL_ORDER, Maze
from ..domain.rules import RULE_CLASSES


@dataclass
class RuleCatalog:
    version: int
    maze: Maze


def load_catalog(path: str | Path, overrides: Optional[dict] = None, allow_pending: bool = False) -> RuleCatalog:
    """Load config/rules/*.yaml. A rule pending calibration cannot run, unless a test or
    simulation passes overrides with allow_pending=True (the values are then not final)."""
    doc = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    cells = doc["scene_maze"]
    if list(cells) != CELL_ORDER:
        raise ContractError(f"catalog must list cells in order {CELL_ORDER}")
    overrides = overrides or {}
    params = {c: dict(cells[c].get("params", {})) for c in CELL_ORDER}
    params["C2"]["expected_boa_add_offset"] = params["A3"]["expected_boa_add_offset"]
    for cell, extra in overrides.items():
        params[cell].update(extra)
    pending = [c for c in CELL_ORDER if cells[c]["status"] == "pending_calibration" and c not in overrides]
    if pending or (overrides and not allow_pending):
        raise ContractError(f"cells pending calibration or overridden without permission: {pending or list(overrides)}")
    rules = [RULE_CLASSES[c](params[c]) for c in CELL_ORDER]
    version = int(doc["version"])
    maze = Maze(rules, {c: version for c in CELL_ORDER}, params)
    return RuleCatalog(version, maze)
