from ..domain.enums import DQCode
from ..domain.errors import ContractError


def check_conservation(scenes_in: int, zone_counts: dict) -> None:
    """Scenes in = validated + rejected + unknown. A mismatch stops the run (DQ-560)."""
    total = sum(zone_counts.get(z, 0) for z in ("validated", "rejected", "unknown"))
    if total != scenes_in:
        raise ContractError(f"{DQCode.DQ_560.value}: {scenes_in} scenes in, {total} accounted for")
