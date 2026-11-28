from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq


def write_evaluations(rows: list, path: str | Path) -> Path:
    """One Parquet file per run, written once and never modified."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise FileExistsError(f"{path} already exists: evaluation files are write-once")
    pq.write_table(pa.Table.from_pylist(rows), path)
    return path
