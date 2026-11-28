from typing import Optional, Sequence

from .enums import State, Subreason
from .models import CellOutcome, Context, Result, VectorOutcome
from .rules import Rule

CELL_ORDER = ["A1", "A2", "A3", "B1", "B2", "B3", "C1", "C2", "C3"]


class Maze:
    """Runs the 9 cells in order and stops at the first cell that is not PASS.

    Always returns exactly one outcome per cell (contract rule F5).
    """

    def __init__(self, rules: Sequence[Rule], versions: dict, thresholds: dict):
        order = [r.cell for r in rules]
        if order != CELL_ORDER:
            raise ValueError(f"maze needs cells in order {CELL_ORDER}, got {order}")
        self.rules = list(rules)
        self.versions = versions
        self.thresholds = thresholds

    def _outcome(self, rule: Rule, result: Result) -> CellOutcome:
        return CellOutcome(rule.cell, result, f"{rule.cell}@{self.versions[rule.cell]}", self.thresholds.get(rule.cell, {}))

    def evaluate(self, ctx: Context, vector: Optional[VectorOutcome] = None) -> list:
        if vector is not None and not vector.open:
            blocked = Result(State.UNKNOWN, Subreason.VECTOR_TRACK_FAILED, f"vector check {vector.failed_check} failed", vector.code)
            return [self._outcome(r, blocked) for r in self.rules]
        outcomes, stopped = [], False
        for rule in self.rules:
            if stopped:
                outcomes.append(self._outcome(rule, Result(State.UNKNOWN, Subreason.NOT_EVALUATED, "not evaluated", None)))
                continue
            result = rule.evaluate(ctx)
            outcomes.append(self._outcome(rule, result))
            if result.state is not State.PASS:
                stopped = True
        return outcomes
