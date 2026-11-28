from typing import Optional, Sequence

from .enums import DQCode, State, Zone
from .models import CellOutcome


def route_zone(outcomes: Sequence[CellOutcome]) -> tuple:
    """Precedence FAIL > UNKNOWN > validated. The code is the first one reported."""
    states = [o.result.state for o in outcomes]
    code = next((o.result.code for o in outcomes if o.result.code is not None), None)
    if State.FAIL in states:
        return Zone.REJECTED, code
    if State.UNKNOWN in states:
        return Zone.UNKNOWN, code
    return Zone.VALIDATED, None
