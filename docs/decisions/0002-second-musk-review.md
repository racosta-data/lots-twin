# 0002. Second Musk review: what was removed, simplified and added

Date: 27 Nov 2026. Maintainer: `racosta-data`. Approved as a block ("implement everything and start building").

| ID | Decision | Reason |
|---|---|---|
| M1 | Remove the `audit_event` table | `evaluation` (9 rows per scene), `run` and the publication manifest already rebuild the path; the table duplicated them |
| M2 | No DuckDB registry in v1 | A1 only needs to know whether `data/raw/<scene_id>` exists. Evaluations are write-once Parquet files per run, and DuckDB queries them directly |
| M3 | Two code packages, `domain` and `pipeline` | The split that matters is pure rules versus everything that touches the world. More layers wait until they hurt |
| M4 | Build the pure rules for all 9 cells first | They are small and let the 20 simulation cases run as tests today. Real measurement (reading files) comes next, starting with A1, A2, B3 and C3 |
| M5 | Freeze new documents until real data exists | Each new document is work without evidence |
| M6 | Add drift alert, `cell_memory`, threshold suggestion, deterministic hash, always-produced mask, minimal CI | They are cheap and they are what turns the design into a system that learns where its walls are, without changing rules by itself |
| M7 | Probe PR7 (PMTiles) after L4 | It is a tooling risk that blocks nothing in the design |
| M8 | C3 stays a gate in v1; reopen after PR4 | Whether low coverage is a wall or a measure needs real distributions |

## Learning policy

What is learned proposes, the rules decide. A learned artifact (memory, alert, threshold suggestion) never changes a result by itself: a change needs a new rule version approved by the maintainer.

Not in v1: learned cell order (the order stays fixed and versioned) and a predictive model (a single territory gives roughly 70 to 150 scenes a year, too few for a model to beat the cloud percentage already present in the metadata; revisit with Atlantico or Colombia).

## Deviation from the proposal

The proposal said to start with 4 cells. The pure rules for all 9 turned out to be a few lines each, and having them makes the 20 simulation cases executable, so all 9 pure rules exist now. What stays staged is the real measurement: the code that reads files and builds the context, starting with A1, A2, B3 and C3.
