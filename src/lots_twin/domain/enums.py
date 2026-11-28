from enum import Enum


class State(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    UNKNOWN = "UNKNOWN"


class Subreason(str, Enum):
    NOT_EVALUATED = "NOT_EVALUATED"
    MISSING_INPUT = "MISSING_INPUT"
    VECTOR_TRACK_FAILED = "VECTOR_TRACK_FAILED"
    RULE_NOT_EFFECTIVE = "RULE_NOT_EFFECTIVE"


class Zone(str, Enum):
    VALIDATED = "validated"
    REJECTED = "rejected"
    UNKNOWN = "unknown"


class DQCode(str, Enum):
    DQ_501 = "DQ-501"  # required field null (V3)
    DQ_506 = "DQ-506"  # unknown state, nothing inferred
    DQ_510 = "DQ-510"  # CRS present but invalid or incoherent (B1)
    DQ_511 = "DQ-511"  # footprint or bbox invalid or incoherent (B2)
    DQ_512 = "DQ-512"  # territory not covered by the scene (B3)
    DQ_520 = "DQ-520"  # usable coverage below threshold (C3)
    DQ_522 = "DQ-522"  # required bands missing (C1)
    DQ_523 = "DQ-523"  # values out of range for the baseline (C2)
    DQ_530 = "DQ-530"  # duplicate scene (A1)
    DQ_531 = "DQ-531"  # unsupported baseline (A3)
    DQ_540 = "DQ-540"  # DANE code missing or hierarchy incoherent (V4)
    DQ_541 = "DQ-541"  # invalid geometry (V1)
    DQ_544 = "DQ-544"  # layer version not effective (V4)
    DQ_550 = "DQ-550"  # hash mismatch or unreadable file (A2)
    DQ_560 = "DQ-560"  # conservation broken
    DQ_570 = "DQ-570"  # publication not verified
