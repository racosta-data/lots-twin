from dataclasses import dataclass, field
from typing import Optional

from .enums import DQCode, State, Subreason


@dataclass(frozen=True)
class Result:
    state: State
    subreason: Optional[Subreason]
    measured: str
    code: Optional[DQCode]


@dataclass(frozen=True)
class CellOutcome:
    cell: str
    result: Result
    rule_version: str
    threshold: dict = field(default_factory=dict)


@dataclass
class Context:
    """Facts already measured about one scene. None means the fact is absent."""

    scene_in_registry: Optional[bool] = None
    hash_published: Optional[str] = None
    hash_received: Optional[str] = None
    file_opens: Optional[bool] = None
    baseline: Optional[str] = None
    crs_metadata: Optional[int] = None
    crs_file: Optional[int] = None
    footprint_valid: Optional[bool] = None
    bbox_matches_raster: Optional[bool] = None
    covered_pct: Optional[float] = None
    bands: Optional[list] = None
    metadata_offset: Optional[int] = None
    max_dn: Optional[int] = None
    usable_coverage_pct: Optional[float] = None


@dataclass
class VectorFacts:
    """Facts about the territory layer. None means absent."""

    geometry_valid: Optional[bool] = True
    attributes_complete: Optional[bool] = True
    code_in_catalog: Optional[bool] = True
    version_effective: Optional[bool] = True


@dataclass(frozen=True)
class VectorOutcome:
    open: bool
    code: Optional[DQCode]
    failed_check: Optional[str]
