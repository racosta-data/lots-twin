# Data Contract v0.2: Geospatial Quality Maze

> Project: `lots-twin`. Territory v1: Barranquilla (DANE `08001`), then Atlántico (`08`), then Colombia (`00`).
> Status: draft v0.2, written before any product code. All artifacts are in English. Values copied from official sources (for example "Barranquilla") are kept exactly as published.

## 0. Decision status

| ID | Decision | Status |
|---|---|---|
| P7 | Viewer consumption event deferred to v2 | Approved |
| B3 | Strict 100% territory coverage in v1 | Approved, revisit with real tile metadata |
| C1 | Required bands stays a cell in row C | Approved, revisit after the data access probe |
| A2/A3 | Stay separate cells | Approved |
| D1 | 4 audit points instead of 8 | Approved |
| D2 | No hash chain on the audit log in v1 (use git for tamper evidence) | Approved |
| D6 | Vector track limited to 3 checks in v1 | Approved |
| D3 | 5 tables; rules live in YAML in git; monthly metric and learning stats are SQL views | Proposed, confirm |
| D4 | One abstract class (`Rule`); everything else concrete until a second implementation exists | Proposed, confirm |
| D5 | No audit decorator on rules; the executor writes the evaluation row | Proposed, confirm |
| D7 | Error catalog reduced to the codes a rule or check actually uses | Proposed, confirm |
| D8 | Integer rule versions (`C3@2`) instead of semantic versions | Proposed, confirm |
| Publication | Scope and viewer (Mapbox or open alternative) | Open |

## 1. Purpose and scope

The contract defines what enters, what is guaranteed on output, how decisions are made and how they are proven.

| Contract | Question it answers |
|---|---|
| Input | What do we accept from the source, and in what form? |
| Output | What do we guarantee in the `validated`, `rejected` and `unknown` zones? |
| Rules | How are rules defined, versioned and changed? |
| Audit and publication | How is everything shown in the viewer reconstructed? |

Out of scope for v1: imputation, interpolation of gaps, silent correction, radar (Sentinel-1), Landsat, events or streaming, microservices, user-query logging (P7), hash-chained audit log.

## 2. Principles

1. **Never invent.** An absent, ambiguous or unevaluable value is rejected with a code or left `UNKNOWN`. It is never filled in.
2. **Rules do not tune themselves.** The system accumulates statistics; only the maintainer changes a threshold, and that creates a new rule version.
3. **Failing is a result, not an exception.** A cloudy scene returns `Result(state=FAIL, code=DQ-520)`. Exceptions are only for infrastructure and contract failures.
4. **Ascending cost.** Cells run from cheap (metadata) to expensive (pixels) and the maze stops at the first non-PASS cell.
5. **Resampling is inventing.** Rasters stay in their native CRS (UTM). The vector is reprojected, which is an exact coordinate transform.
6. **The viewer is derived.** Truth lives in the `validated` zone and the audit log.
7. **Territory is a parameter.** No territory code appears inside a rule.
8. **Eliminate with evidence.** A cell that never fires in 12 months of real data is a candidate for removal.

## 3. Conventions

### 3.1 States

| State | Meaning |
|---|---|
| `PASS` (1) | Evaluated and the rule holds |
| `FAIL` (0) | Evaluated and the rule is violated (a wall) |
| `UNKNOWN` | Not evaluated or not evaluable. Nothing is assumed |

### 3.2 Subreasons (required when the state is `UNKNOWN`)

| Subreason | When |
|---|---|
| `NOT_EVALUATED` | An earlier cell was not PASS, so the maze stopped |
| `MISSING_INPUT` | The data a rule needs is absent. Code `DQ-506` |
| `VECTOR_TRACK_FAILED` | The territory layer failed its checks, so no scene is evaluated against it |
| `RULE_NOT_EFFECTIVE` | No effective version of the rule exists for that date |

### 3.3 Identifiers

| Identifier | Format | Ties together |
|---|---|---|
| `run_id` | UUID | One full execution |
| `scene_id` | Exact product name from the source | One scene across its whole path |
| `territory_code` | DANE code (`00`, `08`, `08001`) | One territory |
| `rule_version` | `cell@integer` (for example `C3@2`) | Exact rule and version |
| `code_version` | Git commit hash | Code that ran |
| `publication_id` | UUID | One package sent to the viewer |

### 3.4 Time and units

UTC, ISO 8601. Percentages in [0, 100] with 2 decimals. Distances in meters, areas in m². Coordinates always travel with their EPSG code.

## 4. Input contract: scene

Source v1: Sentinel-2 level L2A through a public STAC catalog. Access, quotas and license are verified in phase 1.

| Field | Type | Required | Notes |
|---|---|---|---|
| `scene_id` | text | Yes | Unique in the registry (A1) |
| `acquisition_date` | timestamp UTC | Yes | Validated at the ingestion gate by the STAC schema |
| `satellite` | text | Yes | For example Sentinel-2A, 2B, 2C |
| `processing_level` | text | Yes | Must be `L2A` in v1 |
| `baseline` | text | Yes | Processing version; defines the radiometric offset (A3) |
| `crs` | EPSG | Yes | Native (UTM); metadata vs file compared in B1 |
| `bbox` | 4 numbers | Yes | Coherent with the raster (B2) |
| `footprint` | polygon | Yes | Valid geometry (B2) |
| `resolution_m` | number | Yes | Product property, recorded, not a cell |
| `scene_cloud_pct` | % | No | Provider's global metadata. **Does not decide** |
| `territory_cloud_pct` | % | Computed | Clipped to the territory. Informative |
| `usable_coverage` | % | Computed | Observed pixels inside the territory. **Decides in C3** |
| `hash_published` | text | Yes | Hash declared by the source (A2) |
| `hash_received` | text | Computed | Hash of the downloaded file (A2) |
| `territory_code`, `territory_level` | text | Yes | Municipality, department or country |
| `zone` | enum | Computed | `validated`, `rejected`, `unknown` |

Source and license are constants per source and live once in `config/sources/`.

**Observed pixel:** not NoData, not saturated or defective, not cloud (medium or high probability), not cloud shadow and not cirrus. Water, vegetation, bare soil and urban areas count as observed. Water is not a defect.

**Inherited trust (must be declared):** clouds and shadows come from the provider's SCL mask, which is an estimate. The contract calls it "cloud according to SCL". It can fail over very bright surfaces or reflections on water.

**Radiometric trap:** since January 2022 (baseline 04.00) reflectance carries an offset of 1000. C2 reads its range according to the baseline checked in A3, which is why A3 runs before C2.

## 5. Territory and vector track

### 5.1 Entity `territory`

| Field | Type | Required | Notes |
|---|---|---|---|
| `territory_code` | text | Yes | `00`, `08`, `08001` |
| `level` | enum | Yes | `COUNTRY`, `DEPARTMENT`, `MUNICIPALITY` |
| `name` | text | Yes | As published by the source |
| `parent_code` | text | Yes* | Null only for the country |
| `geom` | (multi)polygon | Yes | Reprojected to the raster CRS; the raster is never touched |
| `source_crs` | EPSG | Yes | |
| `layer_version` | text | Yes | Version of the source layer (DANE or IGAC) |
| `updated_on` | date | Yes | |

### 5.2 Vector track (3x1 in v1, runs once per layer version)

If any check fails, no scene is evaluated against that territory and its scenes are `UNKNOWN / VECTOR_TRACK_FAILED`.

| Check | Logic | Error |
|---|---|---|
| **V1** | Geometry valid: no self-intersections, no empty geometry | `DQ-541` |
| **V3** | Required attributes complete | `DQ-501` |
| **V4** | DANE code exists in the catalog with a coherent parent, and the layer version is the effective one | `DQ-540` / `DQ-544` |

V2 (no overlaps between territories) returns in v1.5, when 23 municipalities exist and overlaps have something to be compared with.

## 6. Rules contract: scene maze 3x3

### 6.1 Structure

Rows are ordered by cost. The scene advances and stops at the first non-PASS cell. Later cells become `UNKNOWN / NOT_EVALUATED`.

| Row | Cell | Input | Logic | Error |
|---|---|---|---|---|
| **A. Admission** (metadata, file) | **A1** identity | `scene_id` | Not already in the registry | `DQ-530` |
| | **A2** integrity | file + published hash | Hash matches and the file opens | `DQ-550` |
| | **A3** baseline | `baseline` | In the catalog of supported versions | `DQ-531` |
| **B. Space** | **B1** CRS | metadata + file | Defined and coherent between both | `DQ-510` |
| | **B2** footprint | footprint, bbox, raster | Valid geometry and bbox matches the raster | `DQ-511` |
| | **B3** coverage | footprint + territory polygon | Polygon fully inside the footprint | `DQ-512` |
| **C. Content** (reads pixels) | **C1** bands | band list | Required bands present | `DQ-522` |
| | **C2** value range | clipped pixels | Within range for the baseline offset | `DQ-523` |
| | **C3** usable coverage | clipped SCL mask | `usable_coverage` >= threshold | `DQ-520` / `DQ-521` |

A cell whose input is absent returns `UNKNOWN / MISSING_INPUT / DQ-506`. "Value present but unsupported" is a FAIL; "value absent" is UNKNOWN.

### 6.2 Thresholds

| Cell | v1 value | Status |
|---|---|---|
| B3 | 100% of the polygon inside the footprint | Approved |
| C2 | Range per baseline | Define from product documentation |
| C3 | `null` | **Pending calibration** from 12 months of real Barranquilla data |
| Others | Binary logic | No numeric threshold |

A rule whose threshold is `null` or whose status is `pending_calibration` cannot become effective. The loader raises `ContractError` instead of guessing.

### 6.3 Rule files (`config/rules/`)

One YAML file per version, versioned in git. Fields per cell: `name`, `row`, `cost_rank`, `error_code`, `inputs`, `params`, `status` (`active` or `pending_calibration`). File-level fields: `version` (integer), `effective_from` (date or null), `approved_by`, `justification`.

Changing a threshold or logic creates a new file and a new integer version. Past evaluations keep the version they ran with and are never silently recomputed; reprocessing creates a new `run_id`.

### 6.4 Rule function contract

`evaluate(context) -> Result` is pure: it does not read disk, write, or touch the network. Everything it needs arrives measured in `context`. A `ContextBuilder` in infrastructure computes hashes, CRS, bbox and pixel statistics, and it is **lazy**: row C values are computed only when a cell asks for them, so a duplicate scene that dies in A1 never pays for pixel reads.

## 7. Output contract

### 7.1 Entity `evaluation` (one row per scene and cell)

| Field | Type | Notes |
|---|---|---|
| `run_id`, `scene_id`, `territory_code` | text | |
| `cell` | text | A1 to C3, V1, V3, V4 |
| `state` | enum | `PASS` / `FAIL` / `UNKNOWN` |
| `subreason` | text | Required if `UNKNOWN` |
| `measured_value` | number or text | What was measured, no hidden rounding |
| `threshold_applied` | JSON | Copy of the effective threshold |
| `rule_version` | text | For example `C3@2` |
| `dq_code` | text | Null only if `PASS` |
| `code_version` | text | |
| `evaluated_at` | timestamp UTC | |

### 7.2 Zones

| Zone | Content | Guarantee |
|---|---|---|
| `raw` | Original file as received | Immutable, hashed. Written at ingestion for every scene, before the maze |
| `validated` | Scenes with all 9 cells `PASS` | Zero imputed values |
| `rejected` | Scenes with a `FAIL`, with their code | Always has a reason |
| `unknown` | Scenes not evaluable | Always has a subreason |

Routing precedence: `FAIL` > `UNKNOWN` > validated. Partitioning: `zone/territory_code/year/month/`.

### 7.3 Mask, metrics and conservation

- Observation mask: one COG per scene, clipped to the territory (1 observed, 0 not). It is the proof of "where we know".
- Monthly coverage, temporal gaps and per-cell pass rates are **SQL views** over `evaluation`, not tables. They read all three zones.
- **Conservation invariant:** scenes in = validated + rejected + unknown, checked at each handoff. A mismatch stops the run with `DQ-560`.

## 8. Audit contract

### 8.1 Audit points (D1)

| Point | Covers | Evidence |
|---|---|---|
| **Ingestion** (P0-P2) | Request parameters, catalog reply (count, ids), download (size, duration, retries, hash received vs published) | Stored query, list of ids, hash comparison |
| **Maze** (P3) | Full traversal per scene | `evaluation` rows |
| **Persistence** (P4) | What was written to each zone and how many rows | Counts and file hashes |
| **Publication** (P5-P6) | Layers built, transformations, upload, round-trip result | Manifest and remote status |

P7 (viewer consumption) is deferred to v2.

### 8.2 Entity `audit_event` (append-only)

`event_id`, `run_id`, `point`, `scene_id` (null for batch events), `occurred_at`, `actor`, `payload_hash`. There is no hash chain in v1 (D2): the registry is exported and its manifest hash committed to git, which already makes tampering detectable. The chain returns if an external party requires it.

### 8.3 Entity `run`

`run_id`, `started_at`, `finished_at`, `status`, `code_version`, `dependencies_hash`, `rule_catalog_hash`, `environment`. If the repository has uncommitted changes, the run **refuses to start**.

### 8.4 Not audited

Per-pixel content at every step (the hash is stored, not a copy), performance metrics nobody reads, and debug logs (a separate channel).

## 9. Publication contract

The viewer is a presentation layer, not a source of truth.

### 9.1 Entity `publication` (with embedded manifest)

`publication_id`, `run_id`, `rule_versions` (map cell to version), `files` (name, hash, entity count), `source_crs`, `transformations` (reprojection, simplification tolerance, tiling), `tileset_id`, `tileset_version`, `remote_status`, `active`.

### 9.2 Rules

1. **Round-trip check:** after upload, counts and key properties are compared against the manifest. On mismatch: `DQ-570` and `active = false`; the previous version stays live.
2. **Versioning:** each publication creates a new version and never overwrites.
3. **`UNKNOWN` is visible:** it has its own style (hatched), never transparent. Absence must not read as "no problem".
4. **On-screen statement:** the viewer states that it is derived, that geometries may be simplified, and that it is not for measuring.
5. **Credentials:** a minimal-scope public read token in the client; the secret token only in the publishing process, never in the repository or the browser.

Open: which viewer (Mapbox or an open alternative such as MapLibre with PMTiles) and whether full imagery or only mask and metrics are published. Decided in phase 1 after verifying current limits, quotas and prices.

## 10. Error catalog

Own namespace `DQ-xxx`, separate from HTTP codes.

| Code | Meaning | Source |
|---|---|---|
| `DQ-501` | Required field null | V3 |
| `DQ-506` | Unknown state, nothing inferred | Any cell |
| `DQ-510` | CRS missing, invalid or incoherent | B1 |
| `DQ-511` | Footprint or bbox invalid or incoherent | B2 |
| `DQ-512` | Territory not covered by the scene | B3 |
| `DQ-520` | Usable coverage below threshold | C3 |
| `DQ-521` | NoData above threshold | C3 |
| `DQ-522` | Required bands missing | C1 |
| `DQ-523` | Values out of range for the baseline | C2 |
| `DQ-530` | Duplicate scene | A1 |
| `DQ-531` | Unsupported processing baseline | A3 |
| `DQ-540` | DANE code missing or hierarchy incoherent | V4 |
| `DQ-541` | Invalid geometry | V1 |
| `DQ-544` | Layer version not effective | V4 |
| `DQ-550` | Hash mismatch or unreadable file | A2 |
| `DQ-560` | Conservation broken | Run |
| `DQ-570` | Publication not verified | Publication |

17 codes. Removed from earlier drafts: `502` to `505` (no rule uses them), `542` (V2 deferred), `561` (duplicates `550`) and `571` (no hash chain). Codes `560` and `521` stay because the invariant and the maze diagram need them.

**Exceptions (system failures only):** `InfrastructureError` (disk, network, database unreachable) and `ContractError` (corrupt catalog, invalid schema, rule pending calibration). A rule that fails never raises.

## 11. Null policy

| Situation | Result |
|---|---|
| Required source field absent | `FAIL` + `DQ-501` |
| Data a rule needs does not arrive | `UNKNOWN` + `MISSING_INPUT` + `DQ-506` |
| Cell after a non-PASS cell | `UNKNOWN` + `NOT_EVALUATED` |
| Cloud, shadow or NoData pixel | Not observed; never filled |
| Territory outside the footprint | Rejected; never completed from another scene |
| Any doubt about a value | `UNKNOWN`; never guessed |

## 12. Versioning and change control

- Rules: integer version, one YAML file per version, immutable once effective.
- Contract and schema: this document is versioned in git (`docs/contract/`) and changes through pull requests.
- Every change needs evidence (statistics from real runs), an approver and an effective date.
- Contract owner: the project maintainer, named in `docs/decisions/`.

## 13. Acceptance criteria

| # | Criterion | How it is tested |
|---|---|---|
| 1 | For anything visible on the map, one query returns its full path from request to publication | Traceability query |
| 2 | The conservation equation holds at every handoff | Automatic test per batch |
| 3 | Re-running a historical scene reproduces the same output hash | Reproducibility test |
| 4 | A publication with counts different from its manifest is not activated | Test with a tampered manifest |
| 5 | Editing an exported audit file is detected by the committed manifest hash | Git diff check |
| 6 | `UNKNOWN` areas are visible and distinguishable in the viewer | Visual review |
| 7 | Zero imputed values in the `validated` zone | Pixel-origin audit |
| 8 | The same maze processes Barranquilla and Atlántico without rule changes | Only `territory_code` changes |

## 14. Data model and code mapping

Five tables: `scene`, `evaluation`, `run`, `audit_event`, `publication`. Territories load from `config/territories.yaml`. Rules load from `config/rules/`. Metrics are SQL views. Masks are COG files.

| Contract element | Code component |
|---|---|
| States and errors | `State`, `Subreason`, `DQCode` (enums), `Result` (immutable) |
| Cells | `Rule` (abstract) with one subclass per cell |
| Traversal | `Maze(rows, columns)`, `Traversal` in `domain/` |
| Routing | `domain/routing.py` (`FAIL` > `UNKNOWN` > validated) |
| Measurement | `ContextBuilder` (lazy) in `infrastructure/` |
| Registry | DuckDB behind `registry.py` |
| Audit | `audit_log.py`, append-only |
| Calculations | Pure functions: masks, clipping, statistics |

## 15. Open items

1. STAC catalog to use, access limits and current license.
2. How Barranquilla falls against the scene footprints (real metadata).
3. C3 threshold, calibrated from 12 months of data.
4. Exact radiometric offset rules per baseline.
5. Viewer choice and publication scope; limits, quotas and prices.
6. Current DANE layer version and terms of use.
7. Confirm D3, D4, D5, D7, D8.
8. Name the contract owner in `docs/decisions/`.
