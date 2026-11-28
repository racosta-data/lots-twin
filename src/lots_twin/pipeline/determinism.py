import hashlib
import json

VOLATILE = {"run_id", "evaluated_at"}


def stable_hash(rows: list) -> str:
    """Hash of canonical content: sorted rows, canonical JSON, no timestamps or run ids.
    Never hash raw file bytes that embed metadata (contract section 7.4)."""
    clean = [{k: v for k, v in sorted(r.items()) if k not in VOLATILE} for r in rows]
    clean.sort(key=lambda r: (r["scene_id"], r["cell"]))
    payload = json.dumps(clean, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(payload.encode("ascii")).hexdigest()
