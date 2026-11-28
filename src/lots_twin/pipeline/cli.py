import argparse
import subprocess
import uuid
from pathlib import Path

from .cases import load_cases
from .catalog import load_catalog
from .runner import evaluate_scene
from .storage import write_evaluations

ROOT = Path(__file__).resolve().parents[3]
SIM_OVERRIDES = {"C3": {"min_usable_coverage_pct": 80}}  # simulation placeholder, not a calibrated value


def _git_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return "unknown"


def simulate(args) -> int:
    catalog = load_catalog(ROOT / "config/rules/v1.yaml", overrides=SIM_OVERRIDES, allow_pending=True)
    cases = load_cases(Path(args.fixtures) if args.fixtures else ROOT / "tests/fixtures/cases")
    run_id, rows, diff, commit = str(uuid.uuid4()), [], 0, _git_commit()
    print("NOTE: C3 threshold is a simulation placeholder (80), not a calibrated value.\n")
    for c in cases:
        r, zone, code = evaluate_scene(c.id, "08001", c.ctx, c.vector, catalog, run_id, commit)
        rows.extend(r)
        got = [x["state"] for x in r]
        ok = got == c.cells and zone.value == c.zone and (code.value if code else None) == c.code
        diff += 0 if ok else 1
        print(f"{c.id}  {'MATCH' if ok else 'DIFF '}  {zone.value:<9} {code.value if code else 'none'}")
    print(f"\n{len(cases) - diff} match, {diff} differ")
    if args.parquet:
        print("written:", write_evaluations(rows, args.parquet))
    return 1 if diff else 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="lots-twin")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("simulate", help="run the manual-simulation cases through the maze")
    s.add_argument("--fixtures")
    s.add_argument("--parquet", help="write the evaluation rows to this new Parquet file")
    s.set_defaults(func=simulate)
    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
