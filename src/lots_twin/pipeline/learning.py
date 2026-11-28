from typing import Optional


def suggest_threshold(values: list, bin_width: int = 10) -> dict:
    """Propose a C3 threshold from observed usable_coverage values (0 to 100).

    This is a proposal only: it needs maintainer approval and a new rule version.
    Method 1: the emptiest interior bin that sits between two populated sides (a valley).
    Method 2 (fallback): the value that keeps at least 25% of scenes at or above it.
    """
    if len(values) < 10:
        return {"suggested": None, "method": "none", "note": "need at least 10 scenes"}
    edges = list(range(0, 100 + bin_width, bin_width))
    counts = [sum(1 for v in values if lo <= v < hi or (hi == 100 and v == 100)) for lo, hi in zip(edges, edges[1:])]
    valley: Optional[int] = None
    for i in range(1, len(counts) - 1):
        left, right = max(counts[:i]), max(counts[i + 1:])
        if left > 0 and right > 0 and counts[i] < 0.5 * min(left, right):
            if valley is None or counts[i] < counts[valley]:
                valley = i
    if valley is not None:
        return {"suggested": float(edges[valley + 1]), "method": "valley",
                "note": f"valley in bin {edges[valley]}-{edges[valley + 1]}; proposal, needs approval"}
    ordered = sorted(values)
    cut = ordered[int(len(ordered) * 0.75)]
    return {"suggested": float(cut), "method": "keep_25_percent",
            "note": "no clear valley; value that keeps at least 25% of scenes; proposal, needs approval"}
