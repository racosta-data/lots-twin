class InfrastructureError(Exception):
    """Disk, network or database failure. Never raised by a rule."""


class ContractError(Exception):
    """Corrupt catalog, invalid schema, rule pending calibration, broken conservation (DQ-560)."""
