from .enums import DQCode
from .models import VectorFacts, VectorOutcome


def evaluate_vector_track(facts: VectorFacts) -> VectorOutcome:
    """V1 geometry, V3 attributes, V4 DANE code and layer version. Stops at the first failure."""
    if facts.geometry_valid is None:
        return VectorOutcome(False, DQCode.DQ_506, "V1")
    if not facts.geometry_valid:
        return VectorOutcome(False, DQCode.DQ_541, "V1")
    if facts.attributes_complete is None:
        return VectorOutcome(False, DQCode.DQ_506, "V3")
    if not facts.attributes_complete:
        return VectorOutcome(False, DQCode.DQ_501, "V3")
    if facts.code_in_catalog is None or facts.version_effective is None:
        return VectorOutcome(False, DQCode.DQ_506, "V4")
    if not facts.code_in_catalog:
        return VectorOutcome(False, DQCode.DQ_540, "V4")
    if not facts.version_effective:
        return VectorOutcome(False, DQCode.DQ_544, "V4")
    return VectorOutcome(True, None, None)
