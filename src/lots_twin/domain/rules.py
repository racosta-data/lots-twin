from abc import ABC, abstractmethod

from .enums import DQCode, State, Subreason
from .errors import ContractError
from .models import Context, Result


def _pass(measured: str) -> Result:
    return Result(State.PASS, None, measured, None)


def _fail(code: DQCode, measured: str) -> Result:
    return Result(State.FAIL, None, measured, code)


def _unknown(what: str) -> Result:
    return Result(State.UNKNOWN, Subreason.MISSING_INPUT, f"missing: {what}", DQCode.DQ_506)


class Rule(ABC):
    """One maze cell. evaluate() is pure: it only reads the context it receives."""

    cell: str = ""

    def __init__(self, params: dict | None = None):
        self.params = params or {}

    @abstractmethod
    def evaluate(self, ctx: Context) -> Result: ...


class A1Identity(Rule):
    cell = "A1"

    def evaluate(self, ctx):
        if ctx.scene_in_registry is None:
            return _unknown("scene_in_registry")
        if ctx.scene_in_registry:
            return _fail(DQCode.DQ_530, "scene_in_registry=True")
        return _pass("scene_in_registry=False")


class A2Integrity(Rule):
    cell = "A2"

    def evaluate(self, ctx):
        if ctx.hash_published is None:
            return _unknown("hash_published")
        if ctx.hash_received is None:
            return _unknown("hash_received")
        if ctx.hash_published != ctx.hash_received:
            return _fail(DQCode.DQ_550, "hash mismatch")
        if ctx.file_opens is False:
            return _fail(DQCode.DQ_550, "file does not open")
        return _pass("hash matches")


class A3Baseline(Rule):
    cell = "A3"

    def evaluate(self, ctx):
        if ctx.baseline is None:
            return _unknown("baseline")
        if ctx.baseline not in self.params["supported"]:
            return _fail(DQCode.DQ_531, f"baseline={ctx.baseline}")
        return _pass(f"baseline={ctx.baseline}")


class B1Crs(Rule):
    cell = "B1"

    def evaluate(self, ctx):
        if ctx.crs_metadata is None:
            return _unknown("crs_metadata")
        if ctx.crs_file is None:
            return _unknown("crs_file")
        if ctx.crs_metadata != ctx.crs_file:
            return _fail(DQCode.DQ_510, f"metadata={ctx.crs_metadata} file={ctx.crs_file}")
        return _pass(f"crs={ctx.crs_file}")


class B2Footprint(Rule):
    cell = "B2"

    def evaluate(self, ctx):
        if ctx.footprint_valid is None:
            return _unknown("footprint_valid")
        if ctx.bbox_matches_raster is None:
            return _unknown("bbox_matches_raster")
        if not ctx.footprint_valid or not ctx.bbox_matches_raster:
            return _fail(DQCode.DQ_511, f"footprint_valid={ctx.footprint_valid} bbox_matches={ctx.bbox_matches_raster}")
        return _pass("footprint and bbox coherent")


class B3Coverage(Rule):
    cell = "B3"

    def evaluate(self, ctx):
        if ctx.covered_pct is None:
            return _unknown("covered_pct")
        if ctx.covered_pct < self.params["min_covered_pct"]:
            return _fail(DQCode.DQ_512, f"covered_pct={ctx.covered_pct}")
        return _pass(f"covered_pct={ctx.covered_pct}")


class C1Bands(Rule):
    cell = "C1"

    def evaluate(self, ctx):
        if ctx.bands is None:
            return _unknown("bands")
        missing = [b for b in self.params["required"] if b not in ctx.bands]
        if missing:
            return _fail(DQCode.DQ_522, "missing=" + ",".join(missing))
        return _pass("all required bands")


class C2ValueRange(Rule):
    cell = "C2"

    def evaluate(self, ctx):
        if ctx.metadata_offset is None:
            return _unknown("metadata_offset")
        if ctx.max_dn is None:
            return _unknown("max_dn")
        expected = self.params["expected_boa_add_offset"]
        if ctx.metadata_offset != expected:
            return _fail(DQCode.DQ_523, f"offset={ctx.metadata_offset} expected={expected}")
        if ctx.max_dn > self.params["max_valid_dn"]:
            return _fail(DQCode.DQ_523, f"max_dn={ctx.max_dn}")
        return _pass(f"offset={expected} max_dn={ctx.max_dn}")


class C3UsableCoverage(Rule):
    cell = "C3"

    def evaluate(self, ctx):
        threshold = self.params.get("min_usable_coverage_pct")
        if threshold is None:
            raise ContractError("C3 threshold is null: calibrate it before running (probe PR4)")
        if ctx.usable_coverage_pct is None:
            return _unknown("usable_coverage_pct")
        if ctx.usable_coverage_pct < threshold:
            return _fail(DQCode.DQ_520, f"usable_coverage_pct={ctx.usable_coverage_pct}")
        return _pass(f"usable_coverage_pct={ctx.usable_coverage_pct}")


RULE_CLASSES = {c.cell: c for c in (A1Identity, A2Integrity, A3Baseline, B1Crs, B2Footprint,
                                    B3Coverage, C1Bands, C2ValueRange, C3UsableCoverage)}
